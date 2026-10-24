import pytest

from repurpose.citations import verify_claim, verify_all, normalize

RETRIEVED = {
    "28213613": {
        "title": "Intranasal insulin for Alzheimer disease",
        "abstract": "Insulin signalling in the brain is impaired in Alzheimer disease, and "
                    "intranasal delivery was evaluated in a small randomized trial of older adults.",
    },
    "99999999": {"title": "Unrelated nicotinic receptor review", "abstract": "A review of receptor subtypes."},
}

QUOTE = "Insulin signalling in the brain is impaired in Alzheimer disease"


def test_a_verbatim_quote_from_the_cited_record_passes():
    claim = verify_claim({"text": "brain insulin signalling is impaired", "pmid": "28213613", "quote": QUOTE}, RETRIEVED)
    assert claim["verified"] and claim["failure"] is None


def test_a_fabricated_quote_fails():
    claim = verify_claim({"pmid": "28213613", "quote": "Insulin reverses cognitive decline in every treated patient"}, RETRIEVED)
    assert not claim["verified"]
    assert claim["failure"] == "quote not found in the cited record"


def test_a_real_pmid_with_a_quote_from_a_different_record_fails():
    claim = verify_claim({"pmid": "99999999", "quote": QUOTE}, RETRIEVED)
    assert not claim["verified"]
    assert claim["failure"] == "quote not found in the cited record"


def test_a_pmid_outside_the_retrieved_set_fails_even_when_the_quote_is_real():
    claim = verify_claim({"pmid": "12345678", "quote": QUOTE}, RETRIEVED)
    assert not claim["verified"]
    assert claim["failure"] == "pmid not in retrieved set"


@pytest.mark.parametrize("quote,reason", [
    ("Insulin signalling is impaired", "short"),
    (" ".join(["word"] * 41), "long"),
])
def test_quotes_outside_the_length_window_fail(quote, reason):
    claim = verify_claim({"pmid": "28213613", "quote": quote}, RETRIEVED)
    assert not claim["verified"]
    assert reason in claim["failure"]


def test_unicode_punctuation_and_whitespace_do_not_break_a_real_quote():
    noisy = "Insulin signalling  in the\nbrain is impaired in Alzheimer‐disease"
    record = {"1": {"title": "", "abstract": "Insulin signalling in the brain is impaired in Alzheimer-disease today."}}
    assert verify_claim({"pmid": "1", "quote": noisy}, record)["verified"]
    assert normalize("“quoted”") == '"quoted"'


def test_missing_pmid_fails_and_verify_all_handles_an_empty_list():
    assert verify_claim({"quote": QUOTE}, RETRIEVED)["failure"] == "no pmid"
    assert verify_all([], RETRIEVED) == []
