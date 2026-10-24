"""Retrospective evaluation of graph rankings against independent trial labels."""
from __future__ import annotations

import json
import random
import statistics
from pathlib import Path

import pandas as pd

from .data import digest, write_json
from .graph import assert_no_leakage, build_graph
from .ranking import score_candidates, tie_key


def metrics(order: list[int], positives: set[int]) -> dict:
    if not positives or not positives.issubset(order) or len(order) != len(set(order)):
        raise ValueError("Unique ranking must contain every held-out drug")
    ranks = {drug: rank for rank, drug in enumerate(order, 1)}
    positive_ranks = [ranks[i] for i in positives]
    return {"recall_at_10": sum(r <= 10 for r in positive_ranks) / len(positives),
            "recall_at_20": sum(r <= 20 for r in positive_ranks) / len(positives),
            "mrr": 1 / min(positive_ranks),
            "mean_reciprocal_heldout_rank": statistics.mean(1 / r for r in positive_ranks),
            "hits_at_10": sum(r <= 10 for r in positive_ranks),
            "hits_at_20": sum(r <= 20 for r in positive_ranks)}


def evaluate(root: Path):
    out, processed = root / "artifacts", root / "data/processed"
    manifest = json.loads((out / "manifest.json").read_text())
    ranking = json.loads((out / "rankings.json").read_text())
    labels = json.loads((out / "trial_labels.json").read_text())["labels"]
    positives = {r["drug_id"] for r in labels}
    candidates = sorted(r["drug_id"] for r in ranking)
    if len(candidates) != len(set(candidates)):
        raise ValueError("Duplicate candidates")
    training_path = processed / "training_edges.parquet"
    if digest(training_path) != manifest["training_edges_sha256"]:
        raise ValueError("Training graph changed; rerun prepare before validation")
    edges = pd.read_parquet(training_path)
    targets = {node["id"] for node in manifest["target_diseases"]}
    assert_no_leakage(edges, targets, positives)
    nodes = {n["id"]: n for n in json.loads((processed / "nodes.json").read_text())}
    assert_no_leakage(edges, targets, {i for i, n in nodes.items() if n["type"] == "drug"})
    print("Recomputing degrees and paths from the sanitized training export", flush=True)
    graph = build_graph(edges, nodes)
    recomputed = score_candidates(graph, nodes, targets, candidates)
    cached = {r["drug_id"]: r for r in ranking}
    for row in recomputed:
        previous = cached[row["drug_id"]]
        if row["path_score"] != previous["path_score"] or row["degree"] != previous["degree"]:
            raise ValueError("Cached ranks/degrees disagree with sanitized graph; rerun prepare")
    path = [r["drug_id"] for r in recomputed]
    popularity = [r["drug_id"] for r in sorted(recomputed, key=lambda r: (-r["degree"], tie_key(r["drug_id"])))]
    samples = []
    for seed in range(1000):
        order = list(candidates)
        random.Random(seed).shuffle(order)
        samples.append(metrics(order, positives))
    keys = samples[0].keys()
    random_metrics = {key: statistics.mean(s[key] for s in samples) for key in keys}
    intervals = {key: [sorted(s[key] for s in samples)[24], sorted(s[key] for s in samples)[974]]
                 for key in keys}
    results = {"random": {"status": "available", "metrics": random_metrics,
                          "permutation_95_percent_interval": intervals, "runs": 1000, "seeds": "0..999"},
               "popularity_only": {"status": "available", "metrics": metrics(popularity, positives)},
               "path_only": {"status": "available", "metrics": metrics(path, positives)},
               "embedding_only": {"status": "unavailable", "metrics": None, "reason": "Embedding training is stage 5"},
               "combined": {"status": "unavailable", "metrics": None, "reason": "Requires stage-5 embedding score; LINCS optional"}}
    positions = {method: {drug: rank for rank, drug in enumerate(order, 1)}
                 for method, order in {"path_only": path, "popularity_only": popularity}.items()}
    report = {"evaluation": "retrospective graph-only holdout",
        "ground_truth": "drugs independently tested in Alzheimer's trials; not proven efficacy",
        "candidate_count": len(candidates), "heldout_count": len(positives), "query_count": 1,
        "metric_definitions": {
            "recall_at_k": "Number of held-out drugs in first k positions / all held-out drugs",
            "mrr": "Mean reciprocal first relevant rank across disease queries; one Alzheimer's query here",
            "mean_reciprocal_heldout_rank": "Mean of 1/rank over all held-out drugs; separate from query MRR",
            "random": "Mean of 1000 seeded permutations of the identical candidate universe",
            "random_interval": "2.5th–97.5th percentiles across permutations, not an efficacy interval"},
        "methods": results,
        "heldout_ranks": [{"drug_id": row["drug_id"], "name": row["name"],
                           "ranks": {m: ranks[row["drug_id"]] for m, ranks in positions.items()},
                           "trial_ids": sorted({t["nct_id"] for t in row["trials"]})} for row in labels],
        "audit": {"no_target_drug_edges": True, "cached_path_scores_recomputed": True,
                  "degrees_recomputed": True, "llm_used": False,
                  "training_edges_sha256": manifest["training_edges_sha256"],
                  "rankings_sha256": digest(out / "rankings.json"),
                  "trial_labels_sha256": digest(out / "trial_labels.json")},
        "limitations": ["Trial participation is not efficacy; includes symptomatic treatment studies.",
            "Single disease query: MRR is determined by the first relevant result.",
            "Conservative exact name matching and indication eligibility restrict coverage.",
            "Retrospective edge holdout does not remove historical indirect knowledge or publication bias.",
            "Existing Alzheimer drugs can be rediscovery controls; regulatory status is unverified.",
            "Rank scores are not probabilities; unsigned paths do not establish mechanism.",
            "Embedding and combined results are pending stage 5."]}
    write_json(out / "validation.json", report)
    print(json.dumps(results, indent=2), flush=True)
