"""Pre-compute "Check my idea" results for drugs people commonly try.

These are served straight from disk and labelled "cached", so the obvious demo
queries never spend a live agent run. Anything outside this list still goes through
the normal path, where a live run is available subject to the rate limits.
"""
from __future__ import annotations

import json
from pathlib import Path

from .check import check
from .data import write_json
from .evidence import load_cache
from .resolve import normalize

# Repurposing candidates that come up again and again in Alzheimer's discussion,
# plus the two approved symptomatic drugs people reach for first. Entries that do
# not resolve to a graph node are reported, not silently dropped.
COMMON_QUERIES = [
    "metformin", "rapamycin", "sirolimus", "lithium", "semaglutide", "liraglutide",
    "simvastatin", "atorvastatin", "aspirin", "ibuprofen", "minocycline", "sildenafil",
    "losartan", "dasatinib", "pioglitazone", "rosiglitazone", "candesartan",
    "nilotinib", "bexarotene", "montelukast", "doxycycline", "fluoxetine",
    "verapamil", "allopurinol", "caffeine", "donepezil", "memantine", "insulin detemir",
]


def cache_path(root: Path) -> Path:
    return root / "artifacts/check_cache.json"


def load(root: Path) -> dict:
    path = cache_path(root)
    return json.loads(path.read_text()) if path.exists() else {"queries": {}}


def build(root: Path) -> dict:
    # Export the complete lookup vocabulary, not just discovery candidates. This
    # lets a clean checkout distinguish controls and graph drugs with no path.
    nodes_path = root / "data/processed/nodes.json"
    if nodes_path.exists():
        write_json(root / "artifacts/drug_index.json",
                   [n for n in json.loads(nodes_path.read_text()) if n["type"] == "drug"])
    reviews = load_cache(root)["families"]
    entries, missing = {}, []
    for query in COMMON_QUERIES:
        result = check(root, query, "Alzheimer's disease", evidence_loader=reviews.get)
        result["precomputed"] = True
        entries[normalize(query)] = result
        if result["status"] != "ok":
            missing.append({"query": query, "status": result["status"],
                            "resolved": (result.get("drug") or {}).get("name")})
    report = {"queries": entries, "count": len(entries),
              "resolved": sum(1 for e in entries.values() if e["status"] == "ok"),
              "not_resolved": missing,
              "note": "Pre-computed from the cached agent reviews; served as \"cached\". "
                      "Other inputs still resolve live, subject to the rate limits."}
    write_json(cache_path(root), report)
    print(json.dumps({k: v for k, v in report.items() if k != "queries"}, indent=2))
    return report
