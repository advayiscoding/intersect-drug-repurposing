"""Mixture fitting consumes tuning labels only; test labels are never objectives."""
import json
from pathlib import Path

import pandas as pd

from .data import digest, write_json
from .evaluation import rank_metrics
from .ranking import tie_key


def percentiles(scores):
    # Missing embeddings are below every scored candidate. Equal scores stay tied.
    raw = pd.Series({int(k): (-float("inf") if v is None else float(v)) for k, v in scores.items()})
    ranked = (raw.rank(method="average") - 1) / max(1, len(raw) - 1)
    return ranked.to_dict()


def combined_scores(path_scores, embedding_scores, weight):
    p, e = percentiles(path_scores), percentiles(embedding_scores)
    if set(p) != set(e):
        raise ValueError("Mixture inputs have different universes")
    return {i: (1 - weight) * p[i] + weight * e[i] for i in p}


def ordered(scores, universe):
    return sorted(universe, key=lambda i: (-(scores[i] if scores[i] is not None else -float("inf")), tie_key(i)))


def choose_weight(path_scores, embedding_scores, tuning_ids, tuning_universe, grid):
    if not set(tuning_ids).issubset(tuning_universe):
        raise ValueError("Tuning labels must belong to tuning universe")
    trials = []
    for w in grid:
        scores = combined_scores(path_scores, embedding_scores, w)
        stats = rank_metrics(ordered(scores, tuning_universe), tuning_ids)
        trials.append({"embedding_weight": w, "metrics": stats})
    chosen = max(trials, key=lambda r: (r["metrics"]["recall_at_20"], r["metrics"]["recall_at_10"], -r["embedding_weight"]))
    return chosen["embedding_weight"], trials


def tune(root: Path):
    out = root / "artifacts"
    if (out / "mixture_selection.json").exists():
        raise ValueError("Weights already locked; do not retune after test evaluation")
    protocol = json.loads((out / "protocol.json").read_text())
    run = json.loads((out / "embedding_run.json").read_text())
    if run["config"]["protocol_sha256"] != digest(out / "protocol.json"):
        raise ValueError("Protocol changed after training")
    if run["scores_sha256"] != digest(out / "embedding_scores.json"):
        raise ValueError("Embedding scores changed")
    candidates = set(protocol["candidate_ids"])
    rows = json.loads((out / "rankings.json").read_text())
    paths = {r["drug_id"]: r["path_score"] for r in rows if r["drug_id"] in candidates}
    embeddings = {int(i): score for i, score in json.loads((out / "embedding_scores.json").read_text()).items() if int(i) in candidates}
    weight, trials = choose_weight(paths, embeddings, protocol["tuning_ids"],
                                  protocol["tuning_candidate_ids"], protocol["mixture_grid"])
    write_json(out / "mixture_selection.json", {"embedding_weight": weight, "path_weight": 1-weight,
        "lincs_weight": "unavailable", "trials": trials, "selection_rule": protocol["selection"],
        "fit_label_ids": protocol["tuning_ids"], "test_labels_used": False,
        "protocol_sha256": digest(out / "protocol.json"), "embedding_scores_sha256": run["scores_sha256"],
        "rankings_sha256": digest(out / "rankings.json")})
    print(f"Locked embedding weight {weight} using {len(protocol['tuning_ids'])} tuning labels only", flush=True)
