"""'Check my idea': resolve a drug/disease pair and report what the graph and the
retrieved literature actually say about it.

Only Alzheimer's disease is built. Every claim still passes the same span-level
citation checker, and nothing produced here re-enters the ranking or validation.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .gapmap import verdict_for
from .resolve import DrugIndex, is_supported_disease, sanitize

DISEASE_LABEL = "Alzheimer's disease"
BANNER = "Research hypothesis, not medical advice."
UNSUPPORTED_DISEASE = (
    "Alzheimer's disease is the only disease built in this workbench. The graph, the "
    "ranking and the cached reviews are all Alzheimer-specific, so another disease would "
    "need its own neighborhood and evaluation before anything here could be trusted.")


@lru_cache(maxsize=4)
def _resources(root_str: str):
    root = Path(root_str)
    read = lambda name: json.loads((root / "artifacts" / name).read_text())
    families = read("family_rankings.json")
    family_of = {m["drug_id"]: f for f in families for m in f["members"]}
    return (DrugIndex.load(root), read("explorer_details.json"), family_of,
            {r["drug_id"]: r for r in read("discovery_rankings.json")})


def check(root: Path, drug_text: str, disease_text: str, live: bool = False,
          evidence_loader=None, live_runner=None) -> dict:
    """Resolve the pair and assemble graph paths, evidence and a verdict.

    `evidence_loader(family_id)` returns a cached review or None; `live_runner(family)`
    runs the agents. Both are injected so the flow is testable without a network.
    """
    drug_text, disease_text = sanitize(drug_text), sanitize(disease_text)
    base = {"query": {"drug": drug_text, "disease": disease_text},
            "disease_label": DISEASE_LABEL, "disclaimer": BANNER,
            "scope": "Display only. Nothing here feeds the ranking or the validation metrics."}
    if not drug_text:
        return {**base, "status": "no_drug", "message": "Enter a drug name to check."}
    if not is_supported_disease(disease_text):
        return {**base, "status": "unsupported_disease", "message": UNSUPPORTED_DISEASE}

    index, details, family_of, rankings = _resources(str(root))
    node = index.resolve(drug_text)
    if node is None:
        return {**base, "status": "not_in_graph",
                "message": f"“{drug_text}” is not a drug node in this PrimeKG snapshot. "
                           "That means it is absent from this graph, not that it does not exist.",
                "suggestions": index.suggestions(drug_text)}

    # Everything downstream uses the canonical graph name, never the raw user text.
    drug = {"drug_id": node["id"], "name": node["name"], "source_id": node.get("source_id")}
    detail = details.get(str(node["id"]))
    ranking = rankings.get(node["id"])
    paths = (detail or {}).get("paths", [])
    if not paths:
        reason = ("It is in the graph, but no drug → protein → (protein) → disease path "
                  "reaches an Alzheimer node in the sanitized subgraph, so the path ranking has "
                  "nothing to explain here.")
        if ranking is None:
            reason += (" It is also outside the discovery pool, which only contains drugs with a "
                       "non-Alzheimer indication in PrimeKG.")
        return {**base, "status": "no_path", "drug": drug, "message": reason,
                "in_discovery_pool": ranking is not None}

    family = family_of.get(node["id"])
    result = {**base, "status": "ok", "drug": drug,
              "family": {"id": family["id"], "name": family["name"], "rank": family["rank"],
                         "members": [m["name"] for m in family["members"]]} if family else None,
              "path_score": ranking["path_score"] if ranking else None,
              "path_count": ranking["path_count"] if ranking else len(paths),
              "paths": paths, "graph": (detail or {}).get("graph"),
              "trials": (detail or {}).get("trials", [])}

    cached = evidence_loader(family["id"]) if (evidence_loader and family) else None
    review, freshness, live_error = cached, "cached", None
    if live and family and live_runner:
        try:
            review, freshness = live_runner(family), "live"
        except Exception as error:
            review, freshness, live_error = cached, "cached", str(error)
    if review is None:
        return {**result, "evidence": None, "freshness": "none",
                "live_error": live_error,
                "evidence_message": "No cached review for this drug. Reviews are cached for the "
                                    "top ranked families; none in the retrieved set here."}
    return {**result, "evidence": review, "freshness": freshness, "live_error": live_error,
            **verdict_for(review)}
