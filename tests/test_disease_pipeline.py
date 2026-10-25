import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from repurpose import data, primary_validation

ROOT = Path(__file__).resolve().parents[1]


def fixture_nodes():
    return {i: {"id": i, "name": name, "type": kind, "source_id": str(i)}
            for i, name, kind in [(1, "AD", "disease"), (2, "PD", "disease"),
                                  (3, "Other", "disease"), (4, "Drug A", "drug"),
                                  (5, "Drug B", "drug"), (6, "Gene", "gene/protein")]}


def test_each_disease_gets_fresh_graph_without_either_holdout_orientation():
    from repurpose.disease_pipeline import prepare_graph
    nodes = fixture_nodes()
    rows = [(1, 6, "disease_protein"), (2, 6, "disease_protein"),
            (4, 6, "drug_protein"), (5, 6, "drug_protein"),
            (4, 3, "indication"), (5, 3, "indication")]
    forbidden = [(d, drug, rel) for d in (1, 2) for drug in (4, 5)
                 for rel in ("indication", "off-label use", "contraindication", "unexpected")]
    forbidden += [(v, u, r) for u, v, r in forbidden]
    source = pd.DataFrame(rows + forbidden, columns=["x_index", "y_index", "relation"])
    original = source.copy(deep=True)
    runs = [prepare_graph(source, nodes, {target}, {1, 2}, 3) for target in (1, 2, 1)]
    for result in runs:
        assert len(result["removed"]) == len(forbidden)
        assert not any(result["graph"].has_edge(d, drug) for d in (1, 2) for drug in (4, 5))
    pd.testing.assert_frame_equal(source, original)
    assert dict(runs[0]["graph"].degree()) == dict(runs[2]["graph"].degree())
    runs[0]["graph"].add_edge(1, 4)
    assert not runs[1]["graph"].has_edge(1, 4)
    assert not runs[2]["graph"].has_edge(1, 4)


def test_negative_sampler_guards_all_configured_diseases():
    from repurpose.embeddings import FilteredSampler
    sampler = FilteredSampler(np.array([[0, 0, 4]]), {},
                              ["drug", "drug", "disease", "disease", "disease"], {2, 3}, 5, 1)
    assert sampler.forbidden(np.array([[d, 0, drug] for d in (2, 3) for drug in (0, 1)]
                                     + [[drug, 0, d] for d in (2, 3) for drug in (0, 1)])).all()


def test_parkinson_run_cannot_disable_other_disease_holdout_guard():
    from repurpose.disease_pipeline import run_disease
    with pytest.raises(ValueError, match="all configured disease guards"):
        run_disease(ROOT, "parkinsons", guard_diseases=["parkinsons"])


def test_shared_evaluation_reproduces_frozen_alzheimer_numbers():
    read = lambda name: json.loads((ROOT / "artifacts" / name).read_text())
    protocol = read("protocol.json")
    config = json.loads((ROOT / "config/drug_families.json").read_text())
    result = primary_validation.evaluate_rankings(read("discovery_rankings.json"),
               set(protocol["tuning_ids"] + protocol["test_ids"]), config)
    frozen = read("primary_validation.json")
    def equal(actual, expected):
        if isinstance(expected, dict):
            assert actual.keys() == expected.keys()
            for name in expected:
                equal(actual[name], expected[name])
        elif isinstance(expected, float):
            assert actual == pytest.approx(expected, abs=1e-12, rel=1e-12)
        else:
            assert actual == expected
    for key in ("methods", "family_permutation", "positive_family_count", "candidate_count", "heldout_count"):
        equal(result[key], frozen[key])


def trial(condition, **overrides):
    protocol = {"identificationModule": {"nctId": "NCT00000001"},
                "conditionsModule": {"conditions": [condition]},
                "designModule": {"studyType": "INTERVENTIONAL", "enrollmentInfo": {"type": "ACTUAL", "count": 10},
                                 "designInfo": {"primaryPurpose": "TREATMENT"}},
                "statusModule": {"overallStatus": "COMPLETED"},
                "armsInterventionsModule": {"armGroups": [{"label": "exp", "type": "EXPERIMENTAL"}],
                    "interventions": [{"name": "Drug A", "type": "DRUG", "armGroupLabels": ["exp"]}]}}
    protocol.update(overrides)
    return {"protocolSection": protocol}


def test_trial_matcher_uses_configured_condition_without_widening_drug_matching():
    snapshot = {"studies": [trial("Parkinson's Disease")]}
    assert not data.match_trials(snapshot, fixture_nodes())[0]
    hits, _ = data.match_trials(snapshot, fixture_nodes(), condition_pattern=r"\bparkinson(?:['’]?s)?\s+disease\b")
    assert set(hits) == {4}
    snapshot["studies"][0]["protocolSection"]["designModule"]["enrollmentInfo"]["type"] = "ESTIMATED"
    assert not data.match_trials(snapshot, fixture_nodes(), condition_pattern="parkinson")[0]


def test_configs_resolve_only_explicit_disease_nodes(tmp_path):
    from repurpose.diseases import load_config, resolve_targets
    config = load_config(ROOT, "parkinsons")
    nodes = {n["id"]: {**n, "type": "disease"} for n in config["targets"]}
    targets = resolve_targets(config, nodes)
    assert 28547 in targets
    assert 28540 not in targets  # Wolff-Parkinson-White is not Parkinson's disease.
    with pytest.raises(ValueError):
        resolve_targets(config, {**nodes, 28547: {**nodes[28547], "name": "Wrong entity"}})
    with pytest.raises(ValueError, match="Unknown configured disease"):
        load_config(ROOT, "../parkinsons")
    config["radius"] = 4
    data.write_json(tmp_path / "config/diseases.json", {"diseases": {"parkinsons": config}})
    with pytest.raises(ValueError, match="radius"):
        load_config(tmp_path, "parkinsons")


def test_no_positive_labels_does_not_create_recall():
    result = primary_validation.evaluate_rankings(
        [{"drug_id": 1, "name": "Drug", "path_score": 1, "degree": 1}], set(), {"groups": []})
    assert result["methods"] == {}
    assert result["status"] == "exploratory_no_labels"


def test_cached_alzheimer_replay_preserves_every_path_rank_score_and_degree():
    original = json.loads((ROOT / "artifacts/discovery_rankings.json").read_text())
    replay = json.loads((ROOT / "artifacts/diseases/alzheimers/discovery_rankings.json").read_text())["rankings"]
    fields = ("drug_id", "name", "rank", "path_score", "degree", "path_count", "in_subgraph")
    assert [{k: r[k] for k in fields} for r in original] == [{k: r[k] for k in fields} for r in replay]


def test_cached_disease_runs_keep_controls_out_and_pin_provenance():
    for disease in ("alzheimers", "parkinsons"):
        folder = ROOT / "artifacts/diseases" / disease
        read = lambda name: json.loads((folder / name).read_text())
        report = read("primary_validation.json")
        manifest = read("manifest.json")
        rows = read("discovery_rankings.json")["rankings"]
        labels = read("trial_labels.json")["labels"]
        controls = {r["drug_id"] for r in read("known_controls.json")["controls"]}
        assert not controls & {r["drug_id"] for r in rows}
        assert not controls & {r["drug_id"] for r in labels}
        assert {r["drug_id"] for r in labels} <= {r["drug_id"] for r in rows}
        assert len(labels) == report["heldout_count"] == manifest["label_count"]
        assert len({r["family_id"] for r in labels}) == report["positive_family_count"]
        assert report["provenance"]["rankings_sha256"] == data.digest(folder / "discovery_rankings.json")
        assert manifest["frozen_inputs_sha256"] == data.digest(folder / "frozen_inputs.json")
        assert read("frozen_inputs.json")["scorer_sha256"] == data.digest(ROOT / "src/repurpose/ranking.py")
        for k in (10, 20, 50, 100):
            assert sum(r["rank"] <= k for r in labels) == report["methods"]["path_only"]["metrics"][f"hits_at_{k}"]


def test_checkpoint_report_uses_cached_metrics_and_escapes_text():
    import runpy
    render = runpy.run_path(str(ROOT / "scripts/render_disease_report.py"))["render_report"]
    folder = ROOT / "artifacts/diseases/parkinsons"
    report = json.loads((folder / "primary_validation.json").read_text())
    report["disease_name"] = "<untrusted>"
    manifest = json.loads((folder / "manifest.json").read_text())
    html = render(report, manifest)
    assert "&lt;untrusted&gt;" in html and "<untrusted>" not in html
    assert "0/39" in html and "9.03%" in html and "0.356" in html
    assert report["disclaimer"] in html
    assert "collapsed family cards" in html and "top-k drugs" in html


def test_trial_snapshot_pagination_keeps_configured_query(tmp_path, monkeypatch):
    calls = []
    class Client:
        def get(self, url, params, timeout):
            calls.append(dict(params))
            payload = {"studies": [trial("Parkinson Disease")]}
            if len(calls) == 1:
                payload["nextPageToken"] = "page-two"
            return type("Response", (), {"raise_for_status": lambda self: None,
                                        "json": lambda self: payload})()
    monkeypatch.setattr(data, "session", Client)
    path = tmp_path / "data/raw/parkinsons/trials.json"
    data.fetch_trials(tmp_path, "Parkinson Disease", path)
    snapshot = json.loads(path.read_text())
    assert snapshot["query"] == "Parkinson Disease" and snapshot["pages"] == 2
    assert len(snapshot["studies"]) == 2
    assert all(c["query.cond"] == "Parkinson Disease" for c in calls)
    assert calls[1]["pageToken"] == "page-two"
    assert not (tmp_path / "data/raw/trials.json").exists()


def test_isolated_pipeline_excludes_controls_and_writes_only_disease_outputs(tmp_path, monkeypatch):
    from repurpose import disease_pipeline as pipeline
    nodes = fixture_nodes()
    source = pd.DataFrame([(1, 4, "off-label use"), (4, 1, "off-label use"),
        (2, 4, "off-label use"), (4, 2, "off-label use"),
        (2, 5, "indication"), (5, 2, "indication"),
        (4, 3, "indication"), (5, 3, "indication"),
        (2, 6, "disease_protein"), (4, 6, "drug_protein"), (5, 6, "drug_protein")],
        columns=["x_index", "y_index", "relation"])
    configs = {slug: {"id": slug, "name": name, "radius": 3,
                     "targets": [{"id": i, "name": name}],
                     "label_source": {"provider": "ClinicalTrials.gov", "condition_query": name,
                                      "condition_pattern": name},
                     "controls": {"treatment_names": []}}
               for slug, name, i in [("ad", "AD", 1), ("pd", "PD", 2)]}
    for relative, value in {
        "config/diseases.json": {"diseases": configs, "default_guard_diseases": ["ad", "pd"]},
        "config/drug_families.json": {"groups": []},
        "data/raw/pd/trials.json": {"query": "PD", "retrieved_at": "test-snapshot", "studies": [trial("PD")]},
        "artifacts/primary_validation.json": {"preserve": "Alzheimer frozen result"},
    }.items():
        data.write_json(tmp_path / relative, value)
    (tmp_path / "data/raw/primekg.csv").write_text("fixture source")
    scorer = tmp_path / "src/repurpose/ranking.py"
    scorer.parent.mkdir(parents=True)
    scorer.write_text("fixed scorer fixture provenance")
    monkeypatch.setattr(pipeline, "load_primekg", lambda path: (nodes, source.copy(deep=True)))
    result = pipeline.run_disease(tmp_path, "pd")
    assert result["candidate_count"] == result["heldout_count"] == 1
    assert result["known_controls_excluded"] == 1
    assert result["methods"]["random"]["metrics"]["recall_at_20"] == 1.0
    out = tmp_path / "artifacts/diseases/pd"
    for path in out.glob("*.json"):
        assert "This tool does not tell anyone what to take." in json.loads(path.read_text())["disclaimer"]
    assert json.loads((tmp_path / "artifacts/primary_validation.json").read_text())["preserve"]
    assert not (tmp_path / "artifacts/diseases/ad").exists()
    with pytest.raises(ValueError, match="completed disease run"):
        pipeline.run_disease(tmp_path, "pd")
