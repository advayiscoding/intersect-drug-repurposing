import numpy as np
import pytest

from repurpose.evaluation import bootstrap_recall, rank_metrics


def test_enrichment_and_bootstrap_use_heldout_drug_resampling():
    order = list(range(100))
    positives = {1, 2, 50, 90}
    stats = rank_metrics(order, positives)
    assert stats["recall_at_10"] == .5
    assert stats["enrichment_at_10"] == 5
    assert stats["recall_at_100"] == 1
    ci = bootstrap_recall(order, positives, replicates=10000)
    assert ci["recall_at_10"] == [0, 1]
    assert ci["recall_at_100"] == [1, 1]


def test_recall_denominator_cannot_include_excluded_controls():
    # The protocol supplies the discovery-only universe and positives together.
    with pytest.raises(ValueError):
        rank_metrics([1, 2, 3], {2, 99})
