import json

from repurpose.agents import run_family

RETRIEVAL = {
    "query": "test", "pmids": ["111"], "source": "cache", "retrieved_count": 1,
    "records": {"111": {"pmid": "111", "title": "Insulin and cognition in older adults",
                        "abstract": "A randomized trial reported changes in a memory composite score among participants.",
                        "journal": "J Test", "year": "2020", "publication_types": ["Randomized Controlled Trial"],
                        "url": "https://pubmed.ncbi.nlm.nih.gov/111/"}},
}
FAMILY = {"id": "fam", "name": "Test family", "members": [{"name": "Testodrug"}]}

GOOD = {"pmid": "111", "text": "A trial measured a memory composite.", "evidence_type": "human trial",
        "quote": "A randomized trial reported changes in a memory composite score among participants"}
FABRICATED = {"pmid": "111", "text": "The drug cures the disease.", "evidence_type": "human trial",
              "quote": "the drug reversed dementia in every participant who received it today"}
OFF_SET = {**GOOD, "pmid": "222"}


class StubClient:
    """Returns one good and two bad claims per role; makes no network call."""
    class messages:
        @staticmethod
        def create(**kwargs):
            body = json.dumps({"summary": "s", "direction": "direction unknown", "counter_evidence": "c",
                               "open_questions": ["q"], "claims": [GOOD, FABRICATED, OFF_SET]})
            block = type("Block", (), {"type": "text", "text": body})()
            return type("Message", (), {"content": [block], "stop_reason": "end_turn"})()


def test_only_verifiable_claims_survive_the_citation_check():
    record = run_family(None, FAMILY, RETRIEVAL, client=StubClient())
    assert record["claim_counts"] == {"total": 12, "verified": 4, "failed": 8}
    for section in ("mechanism", "safety", "skeptic", "synthesis"):
        claims = record[section]["claims"]
        assert [c["verified"] for c in claims] == [True, False, False]
        assert claims[1]["failure"] == "quote not found in the cited record"
        assert claims[2]["failure"] == "pmid not in retrieved set"


def test_the_record_carries_scope_direction_and_evidence_tags():
    record = run_family(None, FAMILY, RETRIEVAL, client=StubClient())
    assert record["direction"] == "direction unknown"
    assert record["evidence_types"] == ["human trial"]
    assert "never enters the ranking" in record["scope"]
    assert "not medical advice" in record["disclaimer"]
