import pytest

from repurpose.gapmap import evidence_tier, group_for, verdict_for


def record(claims, direction="direction unknown"):
    """Spread claims across sections the way an agent record stores them."""
    return {"direction": direction, "mechanism": {"claims": claims},
            "safety": {"claims": []}, "skeptic": {"claims": []}, "synthesis": {"claims": []}}


def claim(evidence_type, verified=True):
    return {"text": "t", "pmid": "1", "quote": "q", "evidence_type": evidence_type, "verified": verified}


def test_human_trial_evidence_is_supported():
    assert verdict_for(record([claim("human trial"), claim("review")]))["verdict"] == \
        "supported by human evidence"


def test_preclinical_and_secondary_evidence_only():
    for tag in ("animal", "in vitro", "review", "other"):
        assert verdict_for(record([claim(tag)]))["verdict"] == "animal or in vitro only"


def test_contested_direction_outranks_the_evidence_tier():
    assessment = verdict_for(record([claim("human trial")], "mixed/unclear across variants"))
    assert assessment["verdict"] == "mixed or contested"


def test_opposing_direction_outranks_contested_and_human_evidence():
    assessment = verdict_for(record([claim("human trial")],
                                    "reported as inducing cognitive impairment; evidence is mixed"))
    assert assessment["verdict"] == "possible wrong direction"


def test_enzyme_inhibition_is_not_treated_as_a_wrong_direction():
    # An MAO inhibitor inhibits by design; that is its mechanism, not counter-evidence.
    assessment = verdict_for(record([claim("in vitro")], "inhibits MAO (reported for iproniazid)"))
    assert assessment["verdict"] == "animal or in vitro only"


def test_no_verified_claims_is_absence_in_the_retrieved_set():
    assessment = verdict_for(record([claim("human trial", verified=False)]))
    assert assessment["verdict"] == "none in the retrieved set"
    assert assessment["verified_claims"] == 0
    assert verdict_for(record([]))["verdict"] == "none in the retrieved set"


def test_unverified_claims_never_raise_the_verdict():
    mixed = [claim("human trial", verified=False), claim("animal")]
    assessment = verdict_for(record(mixed))
    assert assessment["verdict"] == "animal or in vitro only"
    assert assessment["evidence_tiers"] == ["animal"]


def test_conflicting_evidence_type_tags_resolve_to_the_strongest_verified_tier():
    # Free-text tags disagree in wording and tier; human evidence must still win,
    # and every tag must land on exactly one normalized tier.
    conflicting = [claim("Animal / in vitro"), claim("in-vitro cell line"),
                   claim("randomized clinical trial in patients"), claim("systematic review")]
    assessment = verdict_for(record(conflicting))
    assert assessment["verdict"] == "supported by human evidence"
    assert assessment["evidence_tiers"] == ["animal", "human trial", "in vitro", "review"]


@pytest.mark.parametrize("tag,tier", [
    ("human trial", "human trial"), ("Human Trial", "human trial"),
    ("clinical", "human trial"), ("trial", "human trial"),
    ("animal", "animal"), ("mouse model", "animal"), ("in vivo rodent", "animal"),
    ("in vitro", "in vitro"), ("cell culture", "in vitro"),
    ("review", "review"), ("meta-analysis", "review"),
    ("", "other"), ("something else", "other"),
])
def test_evidence_tier_normalization(tag, tier):
    assert evidence_tier(tag) == tier


@pytest.mark.parametrize("verdict,trials,group", [
    ("supported by human evidence", 0, "supported but untested"),
    ("animal or in vitro only", 0, "supported but untested"),
    ("mixed or contested", 0, "contested or possible wrong direction"),
    ("possible wrong direction", 0, "contested or possible wrong direction"),
    ("none in the retrieved set", 0, "insufficient evidence retrieved"),
    # A registered trial is a fact and outranks every verdict, including absence.
    ("supported by human evidence", 3, "already in trials"),
    ("possible wrong direction", 1, "already in trials"),
    ("none in the retrieved set", 2, "already in trials"),
])
def test_grouping_rules(verdict, trials, group):
    assert group_for(verdict, trials) == group


def test_a_protective_direction_mentioning_deficits_is_not_a_wrong_direction():
    # "reducing behavioural deficits" is the hypothesis working, not against it.
    protective = ("Animal studies report DHA as ameliorating or reducing disease-associated "
                  "pathology/behavioral deficits (i.e., an inhibitory/protective direction)")
    assert verdict_for(record([claim("animal")], protective))["verdict"] == "animal or in vitro only"


def test_a_drug_reported_to_cause_the_deficit_is_a_wrong_direction():
    harmful = "reported as inducing/contributing to cognitive impairment and neurotoxicity"
    assert verdict_for(record([claim("human trial")], harmful))["verdict"] == "possible wrong direction"
