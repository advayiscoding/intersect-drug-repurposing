"""Freeze eligibility, known controls and a label split before model fitting."""
import hashlib
import json
from pathlib import Path

import pandas as pd

from .data import digest, normalize, write_json


def freeze_protocol(root: Path):
    out = root / "artifacts"
    path = out / "protocol.json"
    if path.exists():
        raise ValueError("Protocol already frozen; do not recreate splits after seeing results")
    manifest = json.loads((out / "manifest.json").read_text())
    rankings = json.loads((out / "rankings.json").read_text())
    labels = json.loads((out / "trial_labels.json").read_text())["labels"]
    nodes = {n["id"]: n for n in json.loads((root / "data/processed/nodes.json").read_text())}
    config = json.loads((root / "config/known_controls.json").read_text())
    targets = {d["id"] for d in manifest["target_diseases"]}
    graph_controls = set()
    # Only inspect unsanitized data for an EXCLUSION registry, never for scores.
    for chunk in pd.read_csv(root / "data/raw/primekg.csv", chunksize=500_000,
                             usecols=["x_index", "y_index", "relation"]):
        mask = (chunk.relation == "indication") & (chunk.x_index.isin(targets) | chunk.y_index.isin(targets))
        for i in set(chunk.loc[mask, "x_index"]) | set(chunk.loc[mask, "y_index"]):
            if nodes[i]["type"] == "drug":
                graph_controls.add(int(i))
    names = {normalize(n) for n in config["treatment_names"]}
    named_controls = {i for i, n in nodes.items() if n["type"] == "drug" and normalize(n["name"]) in names}
    controls = graph_controls | named_controls
    universe = {r["drug_id"] for r in rankings}
    discovery = universe - controls
    positives = {r["drug_id"] for r in labels} & discovery
    # Hash split, fixed salt chosen before fitting or inspecting split-level scores.
    ordered = sorted(positives, key=lambda i: hashlib.sha256(f"20261024-frozen-split:{i}".encode()).hexdigest())
    cut = len(ordered) // 2
    tuning, test = ordered[:cut], ordered[cut:]
    registry = [{"drug_id": i, "name": nodes[i]["name"], "in_original_pool": i in universe,
                 "in_trial_labels": i in {r["drug_id"] for r in labels},
                 "basis": [reason for reason, ids in [("PrimeKG Alzheimer indication", graph_controls),
                                                     ("sourced treatment list", named_controls)] if i in ids]}
                for i in sorted(controls)]
    protocol = {"version": 2, "original_candidate_count": len(universe),
        "candidate_ids": sorted(discovery), "controls": registry,
        "tuning_ids": tuning, "test_ids": test,
        "test_candidate_ids": sorted(discovery - set(tuning)),
        "tuning_candidate_ids": sorted(discovery - set(test)),
        "candidate_policy": "Non-Alzheimer PrimeKG indication, minus known Alzheimer controls. Opposite-split positives excluded from each evaluation universe, never counted as misses.",
        "split": "50/50 deterministic hash split; frozen before embeddings and mixture selection",
        "bootstrap": {"replicates": 10000, "seed": 20261024, "unit": "held-out drug", "interval": "percentile 2.5–97.5%"},
        "mixture_grid": [0.0, 0.25, 0.5, 0.75, 1.0],
        "mixture": "path percentile * (1 - embedding_weight) + embedding percentile * embedding_weight",
        "selection": "Maximize tuning recall@20, then recall@10; ties prefer lower embedding weight. Never use test labels.",
        "primary_rule": "Path is default. Promote tuned combined only if its test recall@20 strictly improves and recall@10 does not decrease; exploratory comparison, not independent efficacy evidence.",
        "training_edges_sha256": manifest["training_edges_sha256"],
        "rankings_sha256": digest(out / "rankings.json"),
        "trial_labels_sha256": digest(out / "trial_labels.json"),
        "controls_config_sha256": digest(root / "config/known_controls.json"),
        "source_history": "Stage-2 aggregate results were already observed; no model or weights were tuned on the new test split. This is retrospective internal evaluation, not a fresh external benchmark."}
    if not tuning or not test:
        raise ValueError("Insufficient positives after exclusions")
    write_json(path, protocol)
    print(json.dumps({"discovery": len(discovery), "controls_in_pool": len(controls & universe),
                      "tuning": len(tuning), "test": len(test), "test_pool": len(protocol["test_candidate_ids"])}, indent=2))
