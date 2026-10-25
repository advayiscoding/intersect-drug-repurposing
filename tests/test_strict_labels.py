import copy

import pytest


def record():
    return {"record_id": "1:NCT00000001:drug", "drug_id": 1, "drug_name": "Drug",
            "protocol": {"eligibilityModule": {"eligibilityCriteria": "Participants must have diagnosed Alzheimer disease."},
                         "descriptionModule": {"briefSummary": "Drug is compared with placebo for cognition."},
                         "outcomesModule": {"primaryOutcomes": [{"measure": "Change in cognition at twelve weeks."}]}}}


def decision():
    return {"record_id": record()["record_id"], "decision": "include", "reasons": [],
            "rationale": "Diagnosed cohort, focal drug and clinical outcome.",
            "evidence": {
                "population": {"field": "eligibilityModule.eligibilityCriteria", "quote": "Participants must have diagnosed Alzheimer disease."},
                "role": {"field": "descriptionModule.briefSummary", "quote": "Drug is compared with placebo for cognition."},
                "clinical": {"field": "outcomesModule.primaryOutcomes.0.measure", "quote": "Change in cognition at twelve weeks."}}}


def test_strict_inclusion_requires_three_source_verified_spans():
    from repurpose.strict_labels import validate_decisions
    assert validate_decisions([record()], [decision()]) == ({1}, {1})
    for gate in ("population", "role", "clinical"):
        changed = copy.deepcopy(decision())
        del changed["evidence"][gate]
        with pytest.raises(ValueError):
            validate_decisions([record()], [changed])


def test_fabricated_or_wrong_field_quote_fails_closed():
    from repurpose.strict_labels import validate_decisions
    changed = decision()
    changed["evidence"]["population"]["quote"] = "Invented diagnosis evidence"
    with pytest.raises(ValueError, match="quote"):
        validate_decisions([record()], [changed])


def test_every_record_requires_exactly_one_decision():
    from repurpose.strict_labels import validate_decisions
    for decisions in ([], [decision(), decision()], [{**decision(), "record_id": "unknown"}]):
        with pytest.raises(ValueError):
            validate_decisions([record()], decisions)


def test_uncertain_and_excluded_records_never_become_positives():
    from repurpose.strict_labels import validate_decisions
    for status in ("uncertain", "exclude"):
        changed = {**decision(), "decision": status, "reasons": ["unclear_population"]}
        # Primary never counts it; the sensitivity set counts only 'uncertain'.
        primary, sensitivity = validate_decisions([record()], [changed])
        assert primary == set()
        assert sensitivity == ({1} if changed["decision"] == "uncertain" else set())


def test_unknown_decision_or_reason_is_rejected():
    from repurpose.strict_labels import validate_decisions
    for changed in ({**decision(), "decision": "probably"},
                    {**decision(), "reasons": ["rank_too_low"]}):
        with pytest.raises(ValueError):
            validate_decisions([record()], [changed])


def test_one_qualifying_study_is_enough_but_drug_counts_once():
    from repurpose.strict_labels import validate_decisions
    other = {**record(), "record_id": "1:NCT00000002:drug"}
    other_decision = {**decision(), "record_id": other["record_id"]}
    assert validate_decisions([record(), other], [decision(), other_decision]) == ({1}, {1})


def test_condition_tag_or_title_alone_cannot_establish_population():
    from repurpose.strict_labels import validate_decisions
    source = record()
    source["protocol"]["conditionsModule"] = {"conditions": ["Alzheimer disease"]}
    changed = decision()
    changed["evidence"]["population"] = {"field": "conditionsModule.conditions.0", "quote": "Alzheimer disease"}
    with pytest.raises(ValueError, match="population"):
        validate_decisions([source], [changed])


def test_exclusion_needs_reason_and_traceable_evidence():
    from repurpose.strict_labels import validate_decisions
    for changed in ({**decision(), "decision": "exclude", "reasons": []},
                    {**decision(), "decision": "exclude", "reasons": ["pk_only"], "evidence": {}}):
        with pytest.raises(ValueError):
            validate_decisions([record()], [changed])


def test_the_sensitivity_set_adds_uncertain_drugs_and_the_primary_set_never_does():
    """docs/STRICT_LABEL_PROTOCOL.md: uncertain is excluded primary, included sensitivity."""
    from repurpose.strict_labels import validate_decisions
    doubtful = {**record(), "record_id": "2:NCT00000003:drug", "drug_id": 2}
    doubtful_decision = {**decision(), "record_id": doubtful["record_id"],
                         "decision": "uncertain", "reasons": ["unclear_population"]}
    primary, sensitivity = validate_decisions([record(), doubtful],
                                             [decision(), doubtful_decision])
    assert primary == {1}
    assert sensitivity == {1, 2}
