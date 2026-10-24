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
    ("supported by human evidence", 0, "evidence retrieved, no trial record found"),
    ("animal or in vitro only", 0, "evidence retrieved, no trial record found"),
    ("mixed or contested", 0, "contested or possible wrong direction"),
    ("possible wrong direction", 0, "contested or possible wrong direction"),
    ("none in the retrieved set", 0, "no evidence retrieved"),
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


def test_a_review_reporting_randomized_trial_results_counts_as_human_evidence():
    # The agent tags the RECORD type; a review of RCTs is still human evidence.
    rct = claim("review")
    rct["quote"] = "Recent randomized controlled trials have demonstrated the efficacy of moclobemide"
    assert verdict_for(record([rct]))["verdict"] == "supported by human evidence"


def test_a_bare_clinical_trial_mention_about_other_drugs_is_not_promoted():
    # "Numerous clinical trials for AD have failed" says nothing about this drug.
    other = claim("review")
    other["quote"] = "Numerous clinical trials of drug candidates for Alzheimer's disease (AD) have failed"
    assert verdict_for(record([other]))["verdict"] == "animal or in vitro only"


def test_the_card_carries_a_tier_breakdown_and_a_supporting_quote():
    good = claim("human trial"); good["quote"] = "a verbatim span"
    assessment = verdict_for(record([claim("animal"), good]))
    assert assessment["evidence_tier_counts"] == {"animal": 1, "human trial": 1}
    assert assessment["supporting_quote"]["evidence_type"] == "human trial"
    assert assessment["supporting_quote"]["quote"] == "a verbatim span"


def test_absence_has_no_supporting_quote():
    assert verdict_for(record([]))["supporting_quote"] is None


def test_disease_relevance_tags_human_evidence_by_condition():
    from repurpose.gapmap import disease_relevance
    ad = claim("human trial"); ad["quote"] = "adults with mild cognitive impairment or Alzheimer's disease"
    other = claim("human trial"); other["quote"] = "children with CLN2 disease between the ages of 3 and 16"
    assert disease_relevance([ad, other])["key"] == "alzheimer"
    assert disease_relevance([other])["key"] == "other"
    assert disease_relevance([claim("animal")])["key"] == "unassessed"
    assert disease_relevance([])["key"] == "unassessed"


def test_relevance_reads_the_quote_not_the_agents_own_sentence():
    # The agent may write "not adults with Alzheimer's"; only the source span counts.
    c = claim("human trial")
    c["quote"] = "a rare lysosomal disorder that causes progressive dementia in children"
    c["text"] = "The trial enrolled children with CLN2, not adults with Alzheimer's disease"
    from repurpose.gapmap import disease_relevance
    assert disease_relevance([c])["key"] == "other"


def test_relevance_never_changes_a_verdict():
    ad = claim("human trial"); ad["quote"] = "patients with Alzheimer's disease"
    other = claim("human trial"); other["quote"] = "patients with psoriasis"
    assert verdict_for(record([ad]))["verdict"] == verdict_for(record([other]))["verdict"]
