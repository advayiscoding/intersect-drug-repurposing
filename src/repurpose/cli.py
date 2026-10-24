"""Offline commands: fetch-trials, prepare, and (stage 2) validate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .data import PRIMEKG_URL, digest, fetch_trials, load_primekg, match_trials, write_json
from .graph import (target_diseases, remove_target_drug_edges, eligible_drugs,
                    neighborhood, build_graph, assert_no_leakage, RELATIONS)
from .ranking import score_candidates


def prepare(root: Path, hops: int):
    raw, processed, out = root / "data/raw", root / "data/processed", root / "artifacts"
    processed.mkdir(parents=True, exist_ok=True)
    print("Reading PrimeKG using pandas", flush=True)
    nodes, edges = load_primekg(raw / "primekg.csv")
    source_rows = len(edges)
    targets = target_diseases(nodes)
    if not targets or not any(nodes[i]["name"] == "Alzheimer disease" for i in targets):
        raise ValueError("Could not resolve Alzheimer's disease in this PrimeKG snapshot")
    drugs = {i for i, node in nodes.items() if node["type"] == "drug"}
    clean, removed = remove_target_drug_edges(edges, targets, drugs)
    candidates = eligible_drugs(clean, nodes, targets)
    del edges
    print(f"Removed {len(removed)} target/drug rows before graph selection", flush=True)
    snapshot = json.loads((raw / "trials.json").read_text())
    matched, match_report = match_trials(snapshot, nodes)
    heldout = set(matched) & set(candidates)
    if not heldout:
        raise ValueError("No eligible independently tested trial drugs matched PrimeKG")
    assert_no_leakage(clean, targets, heldout)
    subset = neighborhood(clean, targets, hops)
    assert_no_leakage(subset, targets, heldout)
    subset.to_parquet(processed / "training_edges.parquet", index=False)
    write_json(processed / "nodes.json", list(nodes.values()))
    # All methods must train/score using this same sanitized export.
    graph = build_graph(subset, nodes)
    print(f"Subgraph: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} pairs", flush=True)
    ranked = score_candidates(graph, nodes, targets, candidates)
    write_json(out / "candidate_paths.json", {str(row["drug_id"]): row["paths"] for row in ranked[:20]})
    write_json(out / "rankings.json", [{k: v for k, v in row.items() if k != "paths"} for row in ranked])
    labels = [{"drug_id": drug, "name": nodes[drug]["name"],
               "trials": sorted(matched[drug], key=lambda x: x["nct_id"])} for drug in sorted(heldout)]
    write_json(out / "trial_labels.json", {"label": "drugs independently tested in Alzheimer's trials",
        "labels": labels, "all_matched_count": len(matched),
        "excluded_outside_candidate_universe": [{"drug_id": i, "name": nodes[i]["name"]}
                                               for i in sorted(set(matched) - heldout)],
        **match_report})
    metadata = {"source": PRIMEKG_URL, "primekg_sha256": digest(raw / "primekg.csv"),
        "trials_sha256": digest(raw / "trials.json"), "trials_retrieved_at": snapshot["retrieved_at"],
        "training_edges_sha256": digest(processed / "training_edges.parquet"),
        "source_nodes": len(nodes), "source_rows": source_rows,
        "target_diseases": [nodes[i] for i in sorted(targets)], "hops": hops,
        "allowed_relations": sorted(RELATIONS), "removed_target_drug_rows": len(removed),
        "removed_relations": {str(k): int(v) for k, v in removed.relation.value_counts().items() if v},
        "graph_nodes": graph.number_of_nodes(), "graph_pairs": graph.number_of_edges(),
        "training_triples": len(subset), "candidates": len(candidates), "heldout_drugs": len(heldout),
        "candidates_with_paths": sum(row["path_score"] > 0 for row in ranked),
        "candidates_outside_subgraph": sum(not row["in_subgraph"] for row in ranked),
        "heldout_outside_subgraph": sorted(heldout - set(graph)),
        "leakage_guard": "passed: all target/drug relationships removed before selection and degrees",
        "direction": "direction unknown", "edge_confidence": "unavailable; uniform evidence weight",
        "candidate_policy": "all PrimeKG drugs with a non-Alzheimer indication; regulatory approval unverified",
        "scope": "research hypotheses; not medical advice"}
    write_json(out / "manifest.json", metadata)
    print(json.dumps({k: metadata[k] for k in ("candidates", "heldout_drugs", "candidates_with_paths", "training_triples")}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["fetch-trials", "prepare", "freeze-protocol", "train-embeddings", "tune", "validate", "validate-primary", "prepare-ui", "build-evidence", "build-gap-map"])
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--hops", type=int, choices=[2, 3], default=3)
    parser.add_argument("--limit", type=int, default=20, help="build-evidence: top N families")
    parser.add_argument("--family", action="append", help="build-evidence: restrict to a family id or name")
    parser.add_argument("--refresh", action="store_true", help="build-evidence: re-run families already cached")
    args = parser.parse_args()
    if args.command == "fetch-trials":
        fetch_trials(args.root)
    elif args.command == "prepare":
        prepare(args.root, args.hops)
    elif args.command == "freeze-protocol":
        from .protocol import freeze_protocol
        freeze_protocol(args.root)
    elif args.command == "train-embeddings":
        from .embeddings import train
        train(args.root)
    elif args.command == "tune":
        from .selection import tune
        tune(args.root)
    elif args.command == "validate-primary":
        from .primary_validation import evaluate_primary
        evaluate_primary(args.root)
    elif args.command == "build-gap-map":
        from .gapmap import build as build_gap_map
        build_gap_map(args.root)
    elif args.command == "build-evidence":
        from .evidence import build
        build(args.root, limit=args.limit, only=args.family, refresh=args.refresh)
    elif args.command == "prepare-ui":
        from .ui_data import prepare_ui
        prepare_ui(args.root)
    else:
        from .validation import evaluate
        evaluate(args.root)


if __name__ == "__main__":
    main()
