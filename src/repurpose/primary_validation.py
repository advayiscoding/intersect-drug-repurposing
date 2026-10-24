"""All-label, untuned-path evaluation with exact intervals and family null test."""
import json
from pathlib import Path

import numpy as np
from scipy.stats import beta, hypergeom

from .data import digest, write_json
from .evaluation import rank_metrics, random_summary
from .families import load_families, family_for
from .selection import ordered


def clopper_pearson(hits, total, confidence=.95):
    if not (0 <= hits <= total and total > 0 and int(hits) == hits):
        raise ValueError("Exact binomial interval needs integer hits and positive total")
    alpha = 1 - confidence
    return [0.0 if hits == 0 else float(beta.ppf(alpha/2, hits, total-hits+1)),
            1.0 if hits == total else float(beta.ppf(1-alpha/2, hits+1, total-hits))]


def family_permutation(family_order, positive_families, repetitions=10000, seed=20261024):
    # Exchangeable family units, each represented once, irrespective of variant count.
    relevant = np.array([f in positive_families for f in family_order], dtype=np.int8)
    rng = np.random.default_rng(seed)
    observed = {k: int(relevant[:k].sum()) for k in (10,20,50)}
    null = {k: [] for k in observed}
    for _ in range(repetitions):
        shuffled = rng.permutation(relevant)
        for k in observed:
            null[k].append(int(shuffled[:k].sum()))
    return {"unit": "one collapsed drug family", "permutations": repetitions, "seed": seed,
        "statistic": "distinct labeled families among the first k collapsed family cards",
        "hypothesis": "uniform random family order, preserving family membership and positive family count",
        "results": {str(k): {"observed": observed[k], "random_mean": float(np.mean(null[k])),
            "p_value_one_sided": float((1 + np.count_nonzero(np.array(null[k]) >= observed[k])) / (repetitions+1))}
            for k in observed},
        "caveat": "Exploratory, post-hoc grouping; k=20 primary family test, k=10/50 descriptive and unadjusted. Not an efficacy test."}


def evaluate_primary(root: Path):
    out = root / "artifacts"
    config, rows, groups = load_families(root)
    protocol = json.loads((out / "protocol.json").read_text())
    if digest(out / "rankings.json") != protocol["rankings_sha256"]:
        raise ValueError("Frozen path input changed")
    positives = set(protocol["tuning_ids"] + protocol["test_ids"])
    universe = [r["drug_id"] for r in rows]
    if set(universe) != set(protocol["candidate_ids"]):
        raise ValueError("Discovery universe changed")
    by_id = {r["drug_id"]: r for r in rows}
    family_ids = {i: family_for(row, config)[0] for i,row in by_id.items()}
    positive_families = {family_ids[i] for i in positives}
    orders = {"path_only": universe,
              "popularity_only": ordered({r["drug_id"]:r["degree"] for r in rows}, universe)}
    methods = {}
    for name, order in orders.items():
        stats = rank_metrics(order, positives)
        ci = {f"recall_at_{k}": clopper_pearson(stats[f"hits_at_{k}"], len(positives)) for k in (10,20,50,100)}
        methods[name] = {"metrics": stats, "exact_95_ci": ci,
            "distinct_families_at_k": {str(k): len({family_ids[i] for i in order[:k] if i in positives}) for k in (10,20,50)}}
    random = random_summary(universe, positives)
    for k in (10,20,50,100):
        random["metrics"][f"recall_at_{k}"] = k/len(universe)
        random["metrics"][f"hits_at_{k}"] = len(positives)*k/len(universe)
        random["metrics"][f"enrichment_at_{k}"] = 1.0
    counts = {f: sum(family_ids[i]==f for i in positives) for f in positive_families}
    methods["random"] = {"metrics": random["metrics"], "exact_95_ci": None,
        "ci_note": "Analytical random recall k/N is a known reference, not a fitted binomial proportion; no CI. MRR is averaged over 1000 permutations.",
        "distinct_families_at_k": {str(k): float(sum(1-hypergeom.pmf(0,len(universe),m,k) for m in counts.values())) for k in (10,20,50)}}
    for name, method in methods.items():
        method["lift"] = {str(k): {
            "vs_random_ratio": method["metrics"][f"recall_at_{k}"]/(k/len(universe)),
            "vs_popularity_percentage_points": 100*(method["metrics"][f"recall_at_{k}"]-methods["popularity_only"]["metrics"][f"recall_at_{k}"])} for k in (10,20,50,100)}
    # Keep the split experiment intact in meaning but replace bootstrap CIs for display.
    split = json.loads((out / "validation.json").read_text())
    for name, result in split["methods"].items():
        result.pop("bootstrap_95_ci", None)
        result.pop("enrichment_95_ci", None)
        result["exact_95_ci"] = ({f"recall_at_{k}": clopper_pearson(result["metrics"][f"hits_at_{k}"],split["heldout_count"]) for k in (10,20,50,100)} if name!="random" else None)
    split["interval_note"] = "Display intervals replaced with Clopper-Pearson; original 22/22 model/weight experiment and scores are unchanged. Random means have no binomial CI."
    split["metric_definitions"] = {k:v for k,v in split["metric_definitions"].items() if "bootstrap" not in k}
    split["limitations"] = [v for v in split["limitations"] if "bootstrap" not in v]
    split["limitations"].append("Exact binomial intervals assume exchangeable drug outcomes; near-duplicate drugs remain correlated.")
    write_json(out / "split_validation.json", split)
    report = {"version": 3, "candidate_count": len(rows), "heldout_count": len(positives),
        "family_count": len(groups), "positive_family_count": len(positive_families), "primary_method": "path_only",
        "methods": methods, "family_permutation": family_permutation([g["id"] for g in groups],positive_families),
        "path_hyperparameters": {"label_fitted": False, "length_penalty": .5, "degree_exponent": -.5, "aggregate_top_paths": 10,
            "note": "All fixed before the first validation run; no label-fitted weights or hyperparameters. Full-44 evaluation is retrospective/descriptive after method selection."},
        "known_controls_excluded": 9,
        "interval_method": "95% Clopper-Pearson exact binomial, integer successes / 44 drugs; drug independence is imperfect, so also examine the family permutation test.",
        "family_metric_note": "Distinct families at k count labeled families recovered in the first k DRUGS. Permutation test uses first k COLLAPSED FAMILY CARDS, a separate ranking unit.",
        "small_sample_note": "The two recovered labels in the earlier 22-drug test at k=20 were insulin detemir and insulin glulisine. The sample is small and these are insulin variants, not independent biological discoveries.",
        "efficacy_note": "Trial participation does not establish efficacy.",
        "embedding_note": "What didn't work: fixed DistMult had 0/22 recall@10/20 on the reserved split. Tuning selected zero embedding weight. Embedding work has stopped.",
        "provenance": {"protocol_sha256": digest(out / "protocol.json"), "families_sha256": digest(root / "config/drug_families.json"), "ranking_sha256": digest(out / "discovery_rankings.json")}}
    write_json(out / "primary_validation.json", report)
    write_json(out / "family_rankings.json", groups)
    print(json.dumps({"drugs":len(rows),"positive_drugs":len(positives),"families":len(groups),"positive_families":len(positive_families),"methods":methods,"permutation":report["family_permutation"]},indent=2))
