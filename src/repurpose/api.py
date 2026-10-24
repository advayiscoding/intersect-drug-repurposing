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
            "evidence":{"cached_family_ids":sorted(cache["families"]),"model":cache.get("model"),
                        "live_available":available(ROOT),"summary":summary(cache)}}


@app.get("/api/drugs/{drug_id}")
def drug_detail(drug_id:int):
    value = artifact("explorer_details.json").get(str(drug_id))
    if value is None:
        raise HTTPException(404, "Drug is not in the discovery candidate pool")
    return value


@app.get("/api/health")
def health():
    from .agents import available
    return {"status":"ok","mode":"cached","primary":"path_only","live_agents_available":available(ROOT)}


@app.get("/api/evidence/{family_id}")
def evidence(family_id:str, live:bool=False):
    """Serve the cached agent review. `live=1` re-runs the agents, falling back to cache."""
    from .evidence import load_cache
    from .agents import available, run_family
    cached = load_cache(ROOT)["families"].get(family_id)
    if not live:
        if cached is None:
            raise HTTPException(404, "No cached literature review for this family")
        return {**cached, "freshness":"cached"}
    if not available(ROOT):
        if cached is None:
            raise HTTPException(503, "Live queries unavailable and nothing cached for this family")
        return {**cached, "freshness":"cached", "live_error":"No API key configured; live queries are unavailable"}
    from .pubmed import retrieve
    family = next((f for f in artifact("family_rankings.json") if f["id"]==family_id), None)
    if family is None:
        raise HTTPException(404, "Unknown family")
    try:
        record = run_family(ROOT, family, retrieve(ROOT, [m["name"] for m in family["members"]]))
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
