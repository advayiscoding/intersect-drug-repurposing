import json
from pathlib import Path

from repurpose.data import digest


def test_cached_report_has_disjoint_controls_splits_and_locked_weights():
    out = Path(__file__).resolve().parents[1] / "artifacts"
    read = lambda name: json.loads((out / name).read_text())
    protocol = read("protocol.json")
    report = read("validation.json")
    selection = read("mixture_selection.json")
    tuning, test = set(protocol["tuning_ids"]), set(protocol["test_ids"])
    controls = {c["drug_id"] for c in protocol["controls"]}
    pool = set(protocol["candidate_ids"])
    assert not tuning & test
    assert not pool & controls
    assert set(protocol["test_candidate_ids"]) == pool - tuning
    assert set(protocol["tuning_candidate_ids"]) == pool - test
    assert set(selection["fit_label_ids"]) == tuning
    assert selection["protocol_sha256"] == digest(out / "protocol.json")
    assert report["heldout_count"] == len(test)
    assert {r["drug_id"] for r in report["heldout_ranks"]} == test
    rows = read("discovery_rankings.json")
    assert {r["drug_id"] for r in rows} == pool
    assert all(r["primary_method"] == report["selected_primary"] for r in rows)
    assert all("bootstrap_95_ci" in result for result in report["methods"].values())
    if selection["embedding_weight"] == 0:
        assert report["methods"]["combined"]["metrics"] == report["methods"]["path_only"]["metrics"]
