"""Offline and budget regression tests: never call a real provider."""
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from repurpose.ratelimit import DailyCap


def test_corrupt_daily_counter_fails_closed(tmp_path):
    path = tmp_path / "runs.json"
    path.write_text("partial write")
    assert DailyCap(path, limit=3).check()["allowed"] is False


@pytest.mark.parametrize("day", ["damaged", "2026-99-99", "2027-01-01"])
def test_invalid_or_future_counter_day_fails_closed(tmp_path, day):
    path = tmp_path / "runs.json"
    path.write_text(json.dumps({"day": day, "count": 3}))
    assert DailyCap(path, limit=3).check(today="2026-10-24")["allowed"] is False


def test_daily_counter_serializes_independent_instances(tmp_path):
    path = tmp_path / "runs.json"
    def consume(_):
        return DailyCap(path, limit=5).check()["allowed"]
    with ThreadPoolExecutor(max_workers=16) as pool:
        assert sum(pool.map(consume, range(100))) == 5
    assert DailyCap(path, limit=5).state()["used"] == 5


def test_drug_index_loads_portable_artifact_without_processed_data(tmp_path):
    from repurpose.resolve import DrugIndex
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "artifacts/drug_index.json").write_text(json.dumps([
        {"id": 1, "name": "Example", "type": "drug", "source_id": "DB1"}]))
    assert DrugIndex.load(tmp_path).resolve("Example")["id"] == 1


def test_offline_mode_overrides_credentials_and_blocks_agent_calls(tmp_path, monkeypatch):
    from repurpose.agents import available, run_family
    monkeypatch.setenv("REPURPOSE_OFFLINE", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-not-a-real-key")
    assert available(tmp_path) is False
    with pytest.raises(RuntimeError, match="Offline mode"):
        run_family(tmp_path, {}, {})


def test_offline_pubmed_cache_miss_never_calls_network(tmp_path, monkeypatch):
    from repurpose.pubmed import search
    monkeypatch.setenv("REPURPOSE_OFFLINE", "1")
    def forbidden(*args, **kwargs):
        pytest.fail("Offline PubMed attempted network")
    monkeypatch.setattr("requests.get", forbidden)
    with pytest.raises(RuntimeError, match="Offline mode"):
        search(tmp_path, "uncached query")


def test_evidence_refresh_obeys_shared_daily_cap(tmp_path, monkeypatch):
    from repurpose import api, agents, evidence, pubmed
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.setenv("REPURPOSE_DAILY_LIVE_CAP", "0")
    monkeypatch.setattr(agents, "available", lambda root: True)
    monkeypatch.setattr(evidence, "load_cache", lambda root: {"families": {"f": {"family_id": "f"}}})
    monkeypatch.setattr(api, "artifact", lambda name: [{"id": "f", "members": [{"name": "Example"}]}])
    def forbidden(*args, **kwargs):
        pytest.fail("Spent budget must prevent retrieval and LLM calls")
    monkeypatch.setattr(pubmed, "retrieve", forbidden)
    result = api.evidence("f", live=True)
    assert result["freshness"] == "cached"
    assert "daily budget" in result["live_error"]


def test_unknown_live_query_does_not_spend_daily_budget(tmp_path, monkeypatch):
    from repurpose import api, agents, evidence, check
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.setattr(agents, "available", lambda root: True)
    monkeypatch.setattr(evidence, "load_cache", lambda root: {"families": {}})
    monkeypatch.setattr(check, "check", lambda *args, **kwargs: {"status": "not_found"})
    assert api.check_idea("unknown", live=True)["daily_cap"]["used"] == 0


def test_live_check_retains_session_quota_metadata(tmp_path, monkeypatch):
    from repurpose import api, agents, evidence, check, pubmed, ratelimit
    monkeypatch.setattr(api, "ROOT", tmp_path)
    monkeypatch.setattr(agents, "available", lambda root: True)
    monkeypatch.setattr(agents, "run_family", lambda *args: {})
    monkeypatch.setattr(pubmed, "retrieve", lambda *args: {})
    monkeypatch.setattr(ratelimit, "limiter", ratelimit.RateLimiter())
    monkeypatch.setattr(evidence, "load_cache", lambda root: {"families": {}})
    monkeypatch.setattr(api, "artifact", lambda name: [{"id": "f", "members": [{"name": "Example"}]}])
    def resolved(*args, **kwargs):
        kwargs["live_runner"]({"id": "f"})
        return {"status": "ok"}
    monkeypatch.setattr(check, "check", resolved)
    assert api.check_idea("Example", live=True)["rate_limit"]["remaining"] == 4


def test_portable_cached_demo_without_secrets_or_processed_data(tmp_path):
    """Copy only shipped inputs; a subprocess cannot reuse the repo's caches."""
    import os
    from pathlib import Path
    import shutil
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[1]
    for directory in ("src/repurpose", "artifacts"):
        shutil.copytree(root / directory, tmp_path / directory,
                        ignore=shutil.ignore_patterns("__pycache__", "screenshots"))
    (tmp_path / "data").mkdir()
    shutil.copyfile(root / "data/synonyms.json", tmp_path / "data/synonyms.json")
    env = {key: value for key, value in os.environ.items()
           if key not in {"ANTHROPIC_API_KEY", "NCBI_API_KEY"}}
    env.update(REPURPOSE_ROOT=str(tmp_path), REPURPOSE_OFFLINE="1",
               PYTHONPATH=str(tmp_path / "src"))
    code = '''
import requests
def forbidden(*args, **kwargs):
    raise AssertionError("Cached demo attempted HTTP")
requests.sessions.Session.request = forbidden
from fastapi.testclient import TestClient
from repurpose.api import app
client = TestClient(app)
overview = client.get("/api/overview")
assert overview.status_code == 200
assert not overview.json()["evidence"]["live_available"]
assert client.get("/api/gap-map").status_code == 200
family = overview.json()["families"][0]
assert client.get(f"/api/drugs/{family['representative_id']}").status_code == 200
for drug in ("metformin", "mecamylamine", "donepezil", "Zzzzzqqq", "Rapamune"):
    response = client.get("/api/check", params={"drug": drug, "live": True})
    assert response.status_code == 200, response.text
    assert not response.json()["live_available"]
review = client.get(f"/api/evidence/{family['id']}", params={"live": True})
assert review.status_code == 200
assert review.json()["freshness"] == "cached"
print("Portable offline API smoke passed")
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
                            env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
