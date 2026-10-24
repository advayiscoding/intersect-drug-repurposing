"""Frozen-split ranking metrics and transparent uncertainty estimates."""
import numpy as np


def rank_metrics(order, positives):
    positives = set(positives)
    if not positives or not positives.issubset(order) or len(order) != len(set(order)):
        raise ValueError("Unique ranking must contain every held-out drug")
    positions = {drug: rank for rank, drug in enumerate(order, 1)}
    ranks = np.array([positions[i] for i in sorted(positives)])
    result = {"mrr": float(1 / ranks.min()),
              "mean_reciprocal_heldout_rank": float(np.mean(1 / ranks))}
    for k in (10, 20, 50, 100):
        hits = int((ranks <= k).sum())
        recall = hits / len(ranks)
        result.update({f"hits_at_{k}": hits, f"recall_at_{k}": recall,
                       f"enrichment_at_{k}": recall / (min(k, len(order)) / len(order))})
    return result


def bootstrap_recall(order, positives, replicates=10000, seed=20261024):
    """Resample positive drugs; fixed candidate pool, rankings and model.

    Percentile intervals measure label-sample variability, not graph/model or
    trial efficacy uncertainty. Sparse zero-hit intervals can be [0, 0].
    """
    positions = {drug: rank for rank, drug in enumerate(order, 1)}
    ranks = np.array([positions[i] for i in sorted(positives)])
    if not len(ranks):
        raise ValueError("No positive labels")
    samples = np.random.default_rng(seed).choice(ranks, (replicates, len(ranks)), replace=True)
    return {f"recall_at_{k}": np.quantile((samples <= k).mean(axis=1), [0.025, 0.975]).tolist()
            for k in (10, 20, 50, 100)}


def summarize(order, positives):
    return {"status": "available", "metrics": rank_metrics(order, positives),
            "bootstrap_95_ci": bootstrap_recall(order, positives)}


def random_summary(universe, positives):
    samples = []
    ranks = []
    ids = sorted(positives)
    for seed in range(1000):
        order = np.random.default_rng(seed).permutation(universe).tolist()
        samples.append(rank_metrics(order, positives))
        positions = {d: r for r, d in enumerate(order, 1)}
        ranks.append([positions[i] for i in ids])
    means = {k: float(np.mean([s[k] for s in samples])) for k in samples[0]}
    # Bootstrap drug-specific recovery rates averaged over fixed random runs.
    resamples = np.random.default_rng(20261024).integers(0, len(ids), (10000, len(ids)))
    intervals = {}
    for k in (10, 20, 50, 100):
        rates = (np.array(ranks) <= k).mean(axis=0)
        intervals[f"recall_at_{k}"] = np.quantile(rates[resamples].mean(axis=1), [.025, .975]).tolist()
    return {"status": "available", "metrics": means, "bootstrap_95_ci": intervals,
            "runs": 1000, "exact_expected_recall": {str(k): min(k, len(universe))/len(universe) for k in (10,20,50,100)},
            "permutation_95_interval": {k: np.quantile([s[k] for s in samples], [.025, .975]).tolist() for k in means}}
