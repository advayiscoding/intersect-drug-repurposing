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
    controls = {c["drug_id"]: c for c in read("known_controls.json")}
    return (DrugIndex.load(root), read("explorer_details.json"), family_of,
            {r["drug_id"]: r for r in read("discovery_rankings.json")}, controls)


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

    index, details, family_of, rankings, controls = _resources(str(root))
    found = index.match(drug_text)
    if found is None:
        return {**base, "status": "not_in_graph",
                "message": f"“{drug_text}” is not a drug node in this PrimeKG snapshot. "
                           "That means it is absent from this graph, not that it does not exist.",
                "suggestions": index.suggestions(drug_text)}

    if found["match_type"] == "ambiguous_synonym":
        return {**base, "status": "ambiguous",
                "message": f"“{found['matched_on']}” is a synonym for more than one drug node in "
                           "this snapshot. Pick the one you meant; nothing is resolved for you.",
                "candidates": [{"drug_id": c["id"], "name": c["name"],
                                "source_id": c.get("source_id")} for c in found["candidates"]]}

    # Everything downstream uses the canonical graph name, never the raw user text.
    node = found["node"]
    drug = {"drug_id": node["id"], "name": node["name"], "source_id": node.get("source_id"),
            "match_type": found["match_type"], "matched_on": found["matched_on"]}
    if found["match_type"] in ("synonym", "prefix"):
        drug["match_note"] = (f"Matched {found['matched_on']} → {node['name']} "
                              f"({'synonym' if found['match_type'] == 'synonym' else 'name prefix'})")
    detail = details.get(str(node["id"]))
    ranking = rankings.get(node["id"])
    paths = (detail or {}).get("paths", [])
    if not paths:
        reason = ("It is in the graph, but no drug → protein → (protein) → disease path "
                  "reaches an Alzheimer node in the sanitized subgraph, so the path ranking has "
                  "nothing to explain here.")
        if node["id"] in controls:
            reason = ("Known Alzheimer's control: excluded from the discovery pool and not "
                      "counted as a miss or discovery. Paths are not assessed in this cached "
                      "discovery view; absence here is not evidence of no biological connection.")
        elif ranking is None:
            reason = ("This graph drug is outside the discovery pool, which requires a "
                      "non-Alzheimer indication in PrimeKG. Paths are not assessed in this "
                      "cached discovery view; absence here is not evidence of no connection.")
        return {**base, "status": "no_path", "drug": drug, "message": reason,
                "in_discovery_pool": ranking is not None,
                "known_control": node["id"] in controls}

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
