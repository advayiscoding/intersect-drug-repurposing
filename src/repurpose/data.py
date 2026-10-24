"""Source snapshots and compact pandas tables; no NetworkX full-graph load."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PRIMEKG_URL = "https://dataverse.harvard.edu/api/access/datafile/6180620"
TRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def session():
    client = requests.Session()
    client.mount("https://", HTTPAdapter(max_retries=Retry(
        total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    client.headers["User-Agent"] = "AlzheimersResearchWorkbench/0.1"
    return client


def fetch_trials(root: Path):
    """Snapshot all query pages; eligibility is applied locally and reproducibly."""
    client = session()
    params = {"query.cond": "Alzheimer Disease", "format": "json", "pageSize": 1000,
              "filter.overallStatus": "COMPLETED,TERMINATED"}
    studies = []
    pages = 0
    while True:
        response = client.get(TRIALS_URL, params=params, timeout=120)
        response.raise_for_status()
        payload = response.json()
        studies.extend(payload.get("studies", []))
        pages += 1
        print(f"Trial snapshot: {len(studies)} records ({pages} pages)", flush=True)
        token = payload.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token
    write_json(root / "data/raw/trials.json", {"source": TRIALS_URL,
        "query": "Alzheimer Disease", "status_filter": "COMPLETED,TERMINATED",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages, "studies": studies})


def load_primekg(path: Path):
    """Read in pandas chunks to avoid retaining duplicated string columns."""
    nodes, edge_parts = {}, []
    for chunk in pd.read_csv(path, chunksize=500_000,
            dtype={"x_id": str, "y_id": str, "x_index": "int32", "y_index": "int32"},
            keep_default_na=False):
        for side in ("x", "y"):
            columns = [f"{side}_{k}" for k in ("index", "id", "type", "name", "source")]
            for index, source_id, kind, name, source in chunk[columns].drop_duplicates().itertuples(index=False, name=None):
                nodes[int(index)] = {"id": int(index), "source_id": source_id,
                                     "type": kind, "name": name, "source": source}
        edge_parts.append(chunk[["x_index", "y_index", "relation", "display_relation"]])
    edges = pd.concat(edge_parts, ignore_index=True)
    for column in ("relation", "display_relation"):
        edges[column] = edges[column].astype("category")
    return nodes, edges


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.casefold())


def match_trials(snapshot: dict, nodes: dict):
    """Conservative exact name/alias matches; never substring or fuzzy matches."""
    lookup = {}
    for node in nodes.values():
        if node["type"] == "drug":
            lookup.setdefault(normalize(node["name"]), []).append(node["id"])
    matched, unmatched, eligible_trials = {}, set(), set()
    for study in snapshot["studies"]:
        p = study["protocolSection"]
        conditions = p.get("conditionsModule", {}).get("conditions", [])
        if not any("alzheimer" in c.casefold() for c in conditions):
            continue
        design = p.get("designModule", {})
        status = p.get("statusModule", {})
        enrollment = design.get("enrollmentInfo", {})
        if (design.get("studyType") != "INTERVENTIONAL"
                or status.get("overallStatus") not in {"COMPLETED", "TERMINATED"}
                or enrollment.get("type") != "ACTUAL" or enrollment.get("count", 0) <= 0
                or design.get("designInfo", {}).get("primaryPurpose") != "TREATMENT"):
            continue
        arms = p.get("armsInterventionsModule", {})
        experimental = {a["label"] for a in arms.get("armGroups", []) if a.get("type") == "EXPERIMENTAL"}
        for intervention in arms.get("interventions", []):
            if intervention.get("type") != "DRUG":
                continue
            if not experimental.intersection(intervention.get("armGroupLabels", [])):
                continue
            names = [intervention["name"], *intervention.get("otherNames", [])]
            hits = {i for name in names for i in lookup.get(normalize(name), [])}
            nct = p["identificationModule"]["nctId"]
            eligible_trials.add(nct)
            if len(hits) != 1:
                unmatched.add(intervention["name"])
                continue
            drug = hits.pop()
            matched.setdefault(drug, []).append({"nct_id": nct,
                "url": f"https://clinicaltrials.gov/study/{nct}",
                "intervention": intervention["name"], "matched_names": names,
                "title": p["identificationModule"].get("briefTitle", ""),
                "status": status["overallStatus"], "enrollment": enrollment["count"]})
    return matched, {"eligible_trials": len(eligible_trials),
                     "unmatched_intervention_names": sorted(unmatched)}
