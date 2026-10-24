import pytest

from repurpose.validation import metrics


def test_recall_and_query_mrr_are_distinct_from_average_positive_reciprocal_rank():
    result = metrics(list(range(1, 31)), {2, 12, 25})
    assert result["recall_at_10"] == pytest.approx(1 / 3)
    assert result["recall_at_20"] == pytest.approx(2 / 3)
    assert result["mrr"] == 0.5
    assert result["mean_reciprocal_heldout_rank"] == pytest.approx((1/2 + 1/12 + 1/25) / 3)


def test_missing_positive_cannot_silently_inflate_recall():
    with pytest.raises(ValueError):
        metrics([1, 2], {2, 3})
