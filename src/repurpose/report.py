"""Evaluate locked scores on the frozen test partition; write cached UI artifacts."""
import json
from pathlib import Path

import pandas as pd

from .data import digest, write_json
from .evaluation import summarize, random_summary
from .graph import assert_no_leakage, build_graph
from .ranking import score_candidates
from .selection import combined_scores, ordered


def evaluate_frozen(root: Path):
    out = root / "artifacts"
    read = lambda name: json.loads((out / name).read_text())
    protocol, selection, run = read("protocol.json"), read("mixture_selection.json"), read("embedding_run.json")
    protocol_hash = digest(out / "protocol.json")
    if any(h != protocol_hash for h in (selection["protocol_sha256"], run["config"]["protocol_sha256"])):
        raise ValueError("Training/selection did not use this frozen protocol")
    if set(selection["fit_label_ids"]) != set(protocol["tuning_ids"]):
        raise ValueError("Mixture fit labels differ from tuning split")
    if set(selection["fit_label_ids"]) & set(protocol["test_ids"]):
        raise ValueError("Test labels leaked into weight selection")
    for name, expected in [("rankings.json", protocol["rankings_sha256"]),
                           ("trial_labels.json", protocol["trial_labels_sha256"]),
                           ("embedding_scores.json", run["scores_sha256"])]:
        if digest(out / name) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    if selection["embedding_scores_sha256"] != run["scores_sha256"]:
        raise ValueError("Mixture selected on different embeddings")
    training_path = root / "data/processed/training_edges.parquet"
    if digest(training_path) != protocol["training_edges_sha256"]:
        raise ValueError("Training triples changed")
    original = read("rankings.json")
    nodes = {n["id"]: n for n in json.loads((root / "data/processed/nodes.json").read_text())}
    edges = pd.read_parquet(training_path)
    targets = {n["id"] for n in read("manifest.json")["target_diseases"]}
    assert_no_leakage(edges, targets, {i for i, n in nodes.items() if n["type"] == "drug"})
    graph = build_graph(edges, nodes)
    recomputed = score_candidates(graph, nodes, targets, [r["drug_id"] for r in original])
    previous = {r["drug_id"]: r for r in original}
    for row in recomputed:
        if any(row[key] != previous[row["drug_id"]][key] for key in ("degree", "path_score")):
            raise ValueError("Cached graph scores failed recomputation audit")
    paths = {r["drug_id"]: r["path_score"] for r in original}
    popularity = {r["drug_id"]: r["degree"] for r in original}
    embeddings = {int(i): score for i, score in read("embedding_scores.json").items()}
    discovery = set(protocol["candidate_ids"])
    mixture = combined_scores({i: paths[i] for i in discovery}, {i: embeddings[i] for i in discovery}, selection["embedding_weight"])
    test_universe, positives = protocol["test_candidate_ids"], set(protocol["test_ids"])
    scores = {"popularity_only": popularity, "path_only": paths, "embedding_only": embeddings, "combined": mixture}
    orders = {method: ordered(values, test_universe) for method, values in scores.items()}
    methods = {"random": random_summary(test_universe, positives)}
    methods.update({m: summarize(order, positives) for m, order in orders.items()})
    for method, result in methods.items():
        result["lift"] = {}
        for k in (10, 20, 50, 100):
            key = f"recall_at_{k}"
            value = result["metrics"][key]
            rand = methods["random"]["metrics"][key]
            pop = methods["popularity_only"]["metrics"][key]
            result["lift"][key] = {"vs_random_ratio": value / rand if rand else None,
                                  "vs_popularity_ratio": value / pop if pop else None,
                                  "vs_random_percentage_points": 100 * (value-rand),
                                  "vs_popularity_percentage_points": 100 * (value-pop),
                                  "zero_baseline_note": "A ratio with zero baseline is undefined; use percentage-point lift."}
            result.setdefault("enrichment_95_ci", {})[f"enrichment_at_{k}"] = [v * len(test_universe)/k for v in result["bootstrap_95_ci"][key]]
    path_stats, combo_stats = methods["path_only"]["metrics"], methods["combined"]["metrics"]
    primary = "combined" if (combo_stats["recall_at_20"] > path_stats["recall_at_20"]
                              and combo_stats["recall_at_10"] >= path_stats["recall_at_10"]) else "path_only"
    embed = methods["embedding_only"]["metrics"]
    embedding_improved = embed["recall_at_20"] > path_stats["recall_at_20"] and embed["recall_at_10"] >= path_stats["recall_at_10"]
    labels = {r["drug_id"]: r for r in read("trial_labels.json")["labels"]}
    rankmaps = {m: {i: r for r, i in enumerate(order, 1)} for m, order in orders.items()}
    # Controls are separate metadata/ranks, excluded from discovery denominators.
    fullmaps = {m: {i: r for r, i in enumerate(ordered(s, sorted(previous)), 1)}
                for m, s in {"path_only": paths, "embedding_only": embeddings, "popularity_only": popularity}.items()}
    controls = [{**c, "ranks_in_original_pool": {m: ranks.get(c["drug_id"]) for m, ranks in fullmaps.items()}}
                for c in protocol["controls"]]
    report = {"protocol_version": 2, "evaluation": "frozen internal retrospective test partition; graph-only",
        "ground_truth": "drugs independently tested in Alzheimer's trials; trial participation does not establish efficacy",
        "original_candidate_count": protocol["original_candidate_count"],
        "discovery_candidate_count": len(discovery), "candidate_count": len(test_universe),
        "heldout_count": len(positives), "tuning_count": len(protocol["tuning_ids"]), "query_count": 1,
        "primary_metrics": ["recall_at_10", "recall_at_20"],
        "methods": methods, "known_controls": controls,
        "metric_definitions": {"recall_at_k": "test positives in first k / all test positives",
            "mrr": "reciprocal first relevant rank for this single disease query",
            "mean_reciprocal_heldout_rank": "mean 1/rank across ALL test positives, including outside top-k",
            "enrichment_at_k": "recall@k divided by exact random expected recall k/N",
            "bootstrap_95_ci": "10000 percentile bootstraps of held-out drugs, seed 20261024, fixed graph/model/pool",
            "random_bootstrap": "resample drug-specific recovery rates averaged over the 1000 fixed random permutations",
            "permutation_95_interval": "between-random-ranking variability; separate from label bootstrap uncertainty"},
        "heldout_ranks": [{"drug_id": i, "name": labels[i]["name"],
            "ranks": {m: ranks[i] for m, ranks in rankmaps.items()},
            "trial_ids": sorted({t["nct_id"] for t in labels[i]["trials"]})} for i in sorted(positives)],
        "selected_primary": primary, "mixture_weights": {"path": selection["path_weight"], "embedding": selection["embedding_weight"], "lincs": "unavailable"},
        "embedding_finding": "Improved primary recall relative to path" if embedding_improved else "Negative finding: embedding did not improve primary recall relative to path",
        "audit": {"no_target_drug_edges_either_direction": True, "degrees_and_paths_recomputed": True,
            "known_controls_excluded_from_discovery_metrics": True,
            "tuning_test_disjoint": True, "negative_sampler_excludes_all_target_drug_pairs": True,
            "test_labels_used_for_weight_fitting": False, "llm_used": False,
            "protocol_sha256": protocol_hash, "training_edges_sha256": protocol["training_edges_sha256"],
            "embedding_model_sha256": run["model_sha256"], "mixture_selection_sha256": digest(out / "mixture_selection.json")},
        "limitations": ["Trial participation does not establish efficacy; symptom studies are included.",
            "Only 22 test drugs; correlated compounds and fixed-graph bootstrap can understate uncertainty.",
            "Zero-hit percentile bootstrap intervals can collapse to zero; this does not imply zero population recall.",
            "Controls are excluded by a conservative source registry; indication does not establish current approval.",
            "Stage-2 aggregate outcomes were previously seen; this is internal retrospective evaluation, not external prospective validation.",
            "Rankings concern lift over random/popularity; graph connectivity and embeddings do not establish mechanism or treatment suitability.",
            "Primary model choice after comparison is exploratory; displayed test performance is not a new independent estimate after selection."]}
    write_json(out / "validation.json", report)
    # Cache all discovery candidates, with controls only in their own registry.
    primary_order = ordered(scores[primary], sorted(discovery))
    rows = []
    for rank, drug in enumerate(primary_order, 1):
        row = dict(previous[drug])
        row.update({"rank": rank, "embedding_score": embeddings[drug], "combined_score": mixture[drug],
                    "primary_method": primary, "signal_weights": {"path": 1.0 if primary == "path_only" else selection["path_weight"],
                    "embedding": 0.0 if primary == "path_only" else selection["embedding_weight"], "lincs": "unavailable"}})
        rows.append(row)
    write_json(out / "discovery_rankings.json", rows)
    explanations = {r["drug_id"]: r["paths"] for r in recomputed}
    write_json(out / "discovery_paths.json", {str(i): explanations[i] for i in primary_order[:20]})
    write_json(out / "known_controls.json", controls)
    print(json.dumps({"primary": primary, "finding": report["embedding_finding"],
                      "methods": {m: r["metrics"] for m, r in methods.items()}}, indent=2), flush=True)
