"""Isolated, fixed-method disease runs; never writes the Alzheimer demo artifacts."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .data import digest, fetch_trials, load_primekg, match_trials, normalize, write_json
from .diseases import DISCLAIMER, load_config, resolve_targets
from .families import family_for, group_rankings
from .graph import (assert_no_leakage, build_graph, eligible_drugs, neighborhood,
                    remove_target_drug_edges)
from .primary_validation import evaluate_rankings
from .ranking import score_candidates


def prepare_graph(source, nodes, targets, guard_targets, radius):
    if not targets or not targets.issubset(guard_targets):
        raise ValueError("Every scoring target must be included in the leakage guard")
    drugs = {i for i, n in nodes.items() if n["type"] == "drug"}
    # Eligibility uses the unsanitized source only as a registry, not as features.
    # Other diseases' guard sets must not silently change this disease's universe.
    candidates = eligible_drugs(source, nodes, targets)
    clean, removed = remove_target_drug_edges(source, guard_targets, drugs)
    assert_no_leakage(clean, guard_targets, drugs)
    subset = neighborhood(clean, targets, radius)
    assert_no_leakage(subset, guard_targets, drugs)
    return {"graph": build_graph(subset, nodes), "training_edges": subset,
            "removed": removed, "candidate_ids": candidates}


def known_controls(source, nodes, targets, config):
    indication = source.loc[(source.relation == "indication") &
                            (source.x_index.isin(targets) | source.y_index.isin(targets))]
    graph_ids = {int(i) for i in set(indication.x_index) | set(indication.y_index)
                 if nodes[i]["type"] == "drug"}
    names = {normalize(n) for n in config["controls"]["treatment_names"]}
    named_ids = {i for i, n in nodes.items() if n["type"] == "drug" and normalize(n["name"]) in names}
    return [{"drug_id": i, "name": nodes[i]["name"],
             "basis": (["PrimeKG target indication"] if i in graph_ids else []) +
                      (["sourced named control"] if i in named_ids else [])}
            for i in sorted(graph_ids | named_ids)]


def fetch_disease_trials(root: Path, disease: str):
    config = load_config(root, disease)
    path = root / "data/raw" / disease / "trials.json"
    if path.exists():
        raise ValueError(f"Trial snapshot already exists: {path}; preserve it")
    fetch_trials(root, config["label_source"]["condition_query"], output_path=path)


def run_disease(root: Path, disease: str, guard_diseases=None, trial_path=None):
    start = time.monotonic()
    config = load_config(root, disease)
    registry = json.loads((root / "config/diseases.json").read_text())
    guards = sorted(set(guard_diseases or registry["default_guard_diseases"]))
    if disease not in guards:
        raise ValueError("The evaluated disease must be in --guard-disease")
    parity_replay = disease == "alzheimers" and guards == ["alzheimers"] and trial_path is not None
    if not parity_replay and not set(registry["default_guard_diseases"]).issubset(guards):
        raise ValueError("Include all configured disease guards; only an explicit Alzheimer snapshot replay is exempt")
    out = root / "artifacts/diseases" / disease
    processed = root / "data/processed/diseases" / disease
    if (out / "manifest.json").exists():
        raise ValueError("A completed disease run exists; do not overwrite after viewing results")
    trial_path = Path(trial_path) if trial_path else root / "data/raw" / disease / "trials.json"
    snapshot = json.loads(trial_path.read_text())
    if snapshot.get("query") != config["label_source"]["condition_query"]:
        raise ValueError("Trial snapshot query does not match the disease config")
    frozen = {"disease": config, "guards": [load_config(root, g) for g in guards],
              "families": json.loads((root / "config/drug_families.json").read_text()),
              "scorer_sha256": digest(root / "src/repurpose/ranking.py"),
              "trial_snapshot_sha256": digest(trial_path), "disclaimer": DISCLAIMER}
    frozen_path = out / "frozen_inputs.json"
    if frozen_path.exists() and json.loads(frozen_path.read_text()) != frozen:
        raise ValueError("Partial-run inputs changed; use a separate experiment directory")
    write_json(frozen_path, frozen)
    source_path = root / "data/raw/primekg.csv"
    print(f"{disease}: fresh pandas load of source PrimeKG", flush=True)
    nodes, source = load_primekg(source_path)
    targets = resolve_targets(config, nodes)
    guard_targets = set().union(*(resolve_targets(c, nodes) for c in frozen["guards"]))
    controls = known_controls(source, nodes, targets, config)
    result = prepare_graph(source, nodes, targets, guard_targets, config["radius"])
    control_ids = {c["drug_id"] for c in controls}
    universe = set(result["candidate_ids"]) - control_ids
    for control in controls:
        control["in_original_pool"] = control["drug_id"] in result["candidate_ids"]
    matched, match_report = match_trials(snapshot, nodes, config["label_source"]["condition_pattern"])
    positives = set(matched) & universe
    graph = result["graph"]
    print(f"{disease}: {graph.number_of_nodes()} graph nodes; {len(universe)} candidates; "
          f"{len(positives)} discovery trial labels", flush=True)
    ranked = score_candidates(graph, nodes, targets, sorted(universe))
    rows = [{k: v for k, v in row.items() if k != "paths"} for row in ranked]
    families = frozen["families"]
    groups = group_rankings(rows, families)
    report = evaluate_rankings(rows, positives, families)
    positions = {row["drug_id"]: row["rank"] for row in ranked}
    labels = [{"drug_id": i, "name": nodes[i]["name"], "rank": positions[i],
               "family_id": family_for(nodes[i] | {"drug_id": i}, families)[0],
               "trials": sorted(matched[i], key=lambda t: t["nct_id"])} for i in sorted(positives)]
    label_report = {"disease_id": disease, "label": f"registered experimental-arm drugs in {config['name']}-tagged trials",
                    "labels": labels, "all_matched_count": len(matched),
                    "controls_in_trial_labels": sorted(set(matched) & control_ids),
                    "excluded_outside_candidate_universe": [{"drug_id": i, "name": nodes[i]["name"]}
                        for i in sorted(set(matched) - set(result["candidate_ids"]))],
                    **match_report, "disclaimer": DISCLAIMER}
    report.update({"disease_id": disease, "disease_name": config["name"],
        "guard_diseases": guards, "known_controls_excluded": len(control_ids & set(result["candidate_ids"])),
        "interval_method": "95% Clopper-Pearson exact binomial; correlated drug variants limit independence.",
        "family_metric_note": "Recovery counts use top-k drugs; the permutation test uses top-k collapsed family cards.",
        "label_definition": label_report["label"],
        "trial_note": "Trial participation does not establish efficacy; retrospective graph holdout, not a temporal test.",
        "label_scope_note": "Registry condition tags and experimental-arm occurrence do not establish disease-patient enrollment or disease-directed testing; healthy-volunteer interaction probes can qualify under the frozen rules.",
        "small_sample_note": "Inspect distinct families as well as drug counts; labels are incomplete and correlated.",
        "path_hyperparameters": {"label_fitted": False, "length_penalty": .5, "degree_exponent": -.5,
                                 "aggregate_top_paths": 10, "explanation_paths": 5},
        "embedding_note": "Not run for this disease. The prior Alzheimer DistMult experiment did not improve primary recall.",
        "lincs": "unavailable", "disclaimer": DISCLAIMER})
    processed.mkdir(parents=True, exist_ok=True)
    result["training_edges"].to_parquet(processed / "training_edges.parquet", index=False)
    write_json(out / "discovery_rankings.json", {"disease_id": disease, "disclaimer": DISCLAIMER, "rankings": rows})
    write_json(out / "candidate_paths.json", {"disease_id": disease, "disclaimer": DISCLAIMER,
               "paths": {str(row["drug_id"]): row["paths"] for row in ranked[:20]}})
    write_json(out / "known_controls.json", {"disease_id": disease, "controls": controls, "disclaimer": DISCLAIMER})
    write_json(out / "family_rankings.json", {"disease_id": disease, "disclaimer": DISCLAIMER, "families": groups})
    write_json(out / "trial_labels.json", label_report)
    report["provenance"] = {"frozen_inputs_sha256": digest(frozen_path),
                            "rankings_sha256": digest(out / "discovery_rankings.json")}
    write_json(out / "primary_validation.json", report)
    manifest = {"disease_id": disease, "disease_name": config["name"],
        "run_at": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic()-start,
        "source_nodes": len(nodes), "source_rows": len(source),
        "target_diseases": [nodes[i] for i in sorted(targets)], "guard_diseases": guards,
        "guard_target_ids": sorted(guard_targets), "negative_sampling_guard_target_ids": sorted(guard_targets),
        "negative_sampling": "Existing filter rejects all guarded target/drug pairs both ways; no embedding training in this pilot.",
        "hops": config["radius"], "removed_target_drug_rows": len(result["removed"]),
        "graph_nodes": graph.number_of_nodes(), "graph_pairs": graph.number_of_edges(),
        "training_triples": len(result["training_edges"]), "original_candidate_count": len(result["candidate_ids"]),
        "candidate_count": len(rows), "label_count": len(positives), "positive_family_count": report["positive_family_count"],
        "candidates_with_paths": sum(r["path_score"] > 0 for r in rows),
        "primekg_sha256": digest(source_path), "trials_sha256": digest(trial_path),
        "trials_retrieved_at": snapshot["retrieved_at"], "frozen_inputs_sha256": digest(frozen_path),
        "training_edges_sha256": digest(processed / "training_edges.parquet"),
        "candidate_policy": "Source PrimeKG non-target indication, minus known controls; regulatory status not asserted.",
        "leakage_guard": "All configured target/drug pairs removed in both directions before neighborhood and degrees.",
        "direction": "direction unknown", "disclaimer": DISCLAIMER}
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"manifest": manifest, "evaluation": report}, indent=2), flush=True)
    return report
