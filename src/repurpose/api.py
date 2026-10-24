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
    return {"families":artifact("family_rankings.json"),"validation":artifact("primary_validation.json"),
            "split":artifact("split_validation.json"),"manifest":artifact("manifest.json"),
            "controls":artifact("known_controls.json"),"evidence_agents_available":False}


@app.get("/api/drugs/{drug_id}")
def drug_detail(drug_id:int):
    value = artifact("explorer_details.json").get(str(drug_id))
    if value is None:
        raise HTTPException(404, "Drug is not in the discovery candidate pool")
    return value


@app.get("/api/health")
def health():
    return {"status":"ok","mode":"cached","primary":"path_only"}


dist = ROOT/"web/dist"
if (dist/"assets").exists():
    app.mount("/assets", StaticFiles(directory=dist/"assets"), name="assets")


@app.get("/")
def index():
    if not (dist/"index.html").exists():
        raise HTTPException(503,"Build the frontend first: cd web && npm run build")
    return FileResponse(dist/"index.html")
