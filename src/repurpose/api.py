"""Read-only cached demo API. Run from the repository root with uvicorn."""
import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(os.environ.get("REPURPOSE_ROOT", Path(__file__).resolve().parents[2]))
app = FastAPI(title="Intersect research workbench", docs_url=None, redoc_url=None)


@lru_cache(maxsize=12)
def artifact(name):
    path = ROOT/"artifacts"/name
    if not path.exists():
        raise HTTPException(503, f"Missing cached artifact: {name}; run prepare-ui / validate-primary")
    return json.loads(path.read_text())


@app.get("/api/overview")
def overview():
    from .agents import available
    from .evidence import load_cache, summary
    cache = load_cache(ROOT)
    return {"families":artifact("family_rankings.json"),"validation":artifact("primary_validation.json"),
            "split":artifact("split_validation.json"),"manifest":artifact("manifest.json"),
            "controls":artifact("known_controls.json"),
            "audited":artifact("audited_validation.json"),
            "plain":artifact("plain_language.json"),
            "evidence":{"cached_family_ids":sorted(cache["families"]),"model":cache.get("model"),
                        "live_available":available(ROOT),"summary":summary(cache)}}


@app.get("/api/drugs/{drug_id}")
def drug_detail(drug_id:int):
    value = artifact("explorer_details.json").get(str(drug_id))
    if value is None:
        raise HTTPException(404, "Drug is not in the discovery candidate pool")
    return value


def _run_live(family, session="anonymous", quota_state=None):
    """The single budgeted entry point for both live UI routes."""
    from .agents import available, run_family
    from .pubmed import retrieve
    from .ratelimit import daily_cap, limiter
    if not available(ROOT):
        raise RuntimeError("Live queries unavailable; offline mode or no API key configured")
    quota = limiter.check(str(session)[:64])
    if quota_state is not None:
        quota_state.update(quota)
    if not quota["allowed"]:
        raise RuntimeError(f"Live checks are limited to {quota['limit']} per "
                           f"{quota['window_seconds'] // 60} minutes for this session")
    budget = daily_cap(ROOT).check()
    if not budget["allowed"]:
        raise RuntimeError(f"The shared daily budget of {budget['limit']} live agent runs "
                           f"is exhausted or unavailable for {budget['day']} (UTC)")
    try:
        return run_family(ROOT, family, retrieve(ROOT, [m["name"] for m in family["members"]]))
    except Exception as error:
        # Provider errors can include request URLs, headers, or private payloads.
        raise RuntimeError(f"Live review failed ({type(error).__name__}); showing cached evidence") from error


@app.get("/api/check")
def check_idea(drug: str = "", disease: str = "Alzheimer's disease", live: bool = False,
               session: str = "anonymous"):
    """Resolve a drug/disease pair. User text is only used to look up a graph node."""
    from .check import check
    from .agents import available
    from .evidence import load_cache
    from .ratelimit import daily_cap
    from .check_cache import load as load_check_cache
    from .resolve import normalize

    if not live:
        precomputed = load_check_cache(ROOT)["queries"].get(normalize(drug))
        if precomputed and normalize(disease) in ("alzheimer", "alzheimers",
                                                  "alzheimer s disease", "alzheimers disease",
                                                  "alzheimer disease"):
            from .agents import available as _available
            return {**precomputed, "freshness": precomputed.get("freshness", "cached"),
                    "live_available": _available(ROOT),
                    "rate_limit": None, "daily_cap": daily_cap(ROOT).state()}

    cache = load_cache(ROOT)["families"]
    quota = {}
    cap = daily_cap(ROOT)
    runner = None
    if live and available(ROOT):
        def runner(family):
            full = next(f for f in artifact("family_rankings.json") if f["id"] == family["id"])
            return _run_live(full, session, quota)
    result = check(ROOT, drug, disease, live=live,
                   evidence_loader=cache.get, live_runner=runner)
    result["live_available"] = available(ROOT)
    result["rate_limit"] = quota or None
    result["daily_cap"] = cap.state()
    return result


@app.get("/api/gap-map")
def gap_map():
    return artifact("gap_map.json")


@app.get("/api/health")
def health():
    from .agents import available
    return {"status":"ok","mode":"cached","primary":"path_only","live_agents_available":available(ROOT)}


@app.get("/api/evidence/{family_id}")
def evidence(family_id:str, live:bool=False, session:str="anonymous"):
    """Serve the cached agent review. `live=1` re-runs the agents, falling back to cache."""
    from .evidence import load_cache
    from .agents import available
    cached = load_cache(ROOT)["families"].get(family_id)
    if not live:
        if cached is None:
            raise HTTPException(404, "No cached literature review for this family")
        return {**cached, "freshness":"cached"}
    if not available(ROOT):
        if cached is None:
            raise HTTPException(503, "Live queries unavailable and nothing cached for this family")
        return {**cached, "freshness":"cached", "live_error":"Offline mode or no API key configured; live queries are unavailable"}
    family = next((f for f in artifact("family_rankings.json") if f["id"]==family_id), None)
    if family is None:
        raise HTTPException(404, "Unknown family")
    try:
        record = _run_live(family, session)
        return {**record, "freshness":"live"}
    except Exception as error:
        if cached is None:
            raise HTTPException(504, f"Live query failed and nothing is cached: {error}")
        return {**cached, "freshness":"cached", "live_error":str(error)}


dist = ROOT/"web/dist"
if (dist/"assets").exists():
    app.mount("/assets", StaticFiles(directory=dist/"assets"), name="assets")


@app.get("/")
def index():
    if not (dist/"index.html").exists():
        raise HTTPException(503,"Build the frontend first: cd web && npm run build")
    return FileResponse(dist/"index.html")
