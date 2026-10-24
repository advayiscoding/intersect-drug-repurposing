"""Build and serve the cached evidence review for the top candidate families."""
from __future__ import annotations

import json
from pathlib import Path

from .agents import available, run_family
from .data import write_json
from .pubmed import retrieve

TOP_FAMILIES = 20


def cache_path(root: Path) -> Path:
    return root / "artifacts/evidence.json"


def load_cache(root: Path) -> dict:
    path = cache_path(root)
    return json.loads(path.read_text()) if path.exists() else {"families": {}, "model": None}


def build(root: Path, limit: int = TOP_FAMILIES, only: list[str] | None = None, refresh: bool = False) -> dict:
    """Run the agents per family (never per variant) and cache verified output."""
    families = json.loads((root / "artifacts/family_rankings.json").read_text())[:limit]
    if only:
        families = [f for f in families if f["id"] in only or f["name"] in only]
    cache = load_cache(root)
    if not available(root):
        raise RuntimeError("ANTHROPIC_API_KEY is not set; cached evidence cannot be built")
    for family in families:
        if not refresh and family["id"] in cache["families"]:
            print(f"skip {family['name']} (cached)", flush=True)
            continue
        retrieval = retrieve(root, [m["name"] for m in family["members"]])
        record = run_family(root, family, retrieval)
        cache["families"][family["id"]] = record
        cache["model"] = record["model"]
        counts = record["claim_counts"]
        print(f"{family['name']}: {record['retrieval']['retrieved_count']} records, "
              f"{counts['verified']}/{counts['total']} claims verified", flush=True)
        write_json(cache_path(root), cache)
    write_json(cache_path(root), cache)
    totals = summary(cache)
    print(json.dumps(totals, indent=2))
    return cache


def summary(cache: dict) -> dict:
    families = cache.get("families", {})
    total = sum(f["claim_counts"]["total"] for f in families.values())
    verified = sum(f["claim_counts"]["verified"] for f in families.values())
    with_claim = sum(1 for f in families.values() if f["claim_counts"]["verified"] > 0)
    return {"families_cached": len(families), "families_with_a_verified_claim": with_claim,
            "claims_total": total, "claims_verified": verified, "claims_failed": total - verified,
            "failure_rate": round((total - verified) / total, 4) if total else None}
