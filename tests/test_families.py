import pytest
from repurpose.families import family_for, group_rankings
from repurpose.primary_validation import clopper_pearson, family_permutation


def test_exact_intervals_do_not_collapse_when_no_hits():
    low, high = clopper_pearson(0, 44)
    assert low == 0
    assert high == pytest.approx(0.08041994, abs=1e-7)
    assert clopper_pearson(44, 44)[1] == 1


def test_family_grouping_does_not_multiply_family_recovery():
    config = {"groups": [{"id": "insulin", "name": "Insulin variants", "prefixes": ["insulin "]}]}
    rows = [{"drug_id": i, "name": name, "path_score": 1} for i,name in enumerate(["Insulin aspart", "Insulin glulisine", "Choline"])]
    groups = group_rankings(rows, config)
    assert len(groups) == 2 and len(groups[0]["members"]) == 2
    perm = family_permutation([f"f{i}" for i in range(100)], {"f0"}, repetitions=1000)
    assert perm["results"]["10"]["observed"] == 1
    assert 0 < perm["results"]["10"]["p_value_one_sided"] < .2
