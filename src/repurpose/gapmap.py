"""Deterministic evidence gap map over the cached agent reviews.

Display-only triage. Nothing here feeds the ranking or the validation metrics.
Every input is already in the repository: the frozen path ranking, the VERIFIED
agent claims, and the existing matched ClinicalTrials.gov records.
"""
from __future__ import annotations

import json
from pathlib import Path

from .data import write_json

# Reported effects that run against the repurposing hypothesis. "inhibit" is
# deliberately absent: enzyme inhibition is the intended mechanism of many drugs
# here (an MAO inhibitor, for instance) and is not evidence of a wrong direction.
OPPOSING = ("block", "antagoni", "abolish", "oppos", "exacerbat", "worsen", "detriment")
# A harm verb AND a harm noun together read as "the drug causes the deficit".
# Either alone is ambiguous: "reducing behavioural deficits" is protective.
HARM_VERBS = ("induc", "caus", "contribut", "produc", "lead to", "result in")
HARM_NOUNS = ("impair", "deficit", "toxicit", "decline", "dysfunction", "damage")
PROTECTIVE = ("amelior", "attenuat", "protect", "improv", "reduc", "decreas",
              "slow", "rescu", "restor", "prevent")
CONTESTED = ("mixed", "unclear", "conflict", "contested", "inconsistent",
             "not uniform", "varies", "vary", "contradict")


def direction_signal(direction: str) -> str:
    """Classify the reported direction as opposing, contested or neutral."""
    text = (direction or "").casefold()
    if any(word in text for word in OPPOSING):
        return "opposing"
    harm = any(v in text for v in HARM_VERBS) and any(n in text for n in HARM_NOUNS)
    if harm and not any(word in text for word in PROTECTIVE):
        return "opposing"
    if any(word in text for word in CONTESTED):
        return "contested"
    return "neutral"

VERDICTS = ("supported by human evidence", "animal or in vitro only",
            "mixed or contested", "possible wrong direction", "none in the retrieved set")

GROUPS = ("already in trials", "contested or possible wrong direction",
          "supported but untested", "insufficient evidence retrieved")


def evidence_tier(tag: str) -> str:
    """Normalize a free-text evidence_type tag onto a fixed tier."""
    tag = (tag or "").strip().casefold()
    if "animal" in tag or "in vivo" in tag or "mouse" in tag or "rodent" in tag:
        return "animal"
    if "vitro" in tag or "cell" in tag:
        return "in vitro"
    if "human" in tag or "clinical" in tag or tag.startswith("trial") or "patient" in tag:
        return "human trial"
    if "review" in tag or "meta" in tag:
        return "review"
    return "other"


def verdict_for(record: dict) -> dict:
    """Derive the verdict from VERIFIED claims and the reported direction only.

    Order matters and is fixed: an opposing direction outranks a contested one,
    which outranks the evidence tier. Unverified claims are ignored entirely.
    """
    verified = [claim for section in ("mechanism", "safety", "skeptic", "synthesis")
                for claim in record.get(section, {}).get("claims", []) if claim.get("verified")]
    tiers = sorted({evidence_tier(claim.get("evidence_type")) for claim in verified})
    signal = direction_signal(record.get("direction") or "")

    if not verified:
        verdict = "none in the retrieved set"
    elif signal == "opposing":
        verdict = "possible wrong direction"
    elif signal == "contested":
        verdict = "mixed or contested"
    elif "human trial" in tiers:
        verdict = "supported by human evidence"
    else:
        verdict = "animal or in vitro only"
    return {"verdict": verdict, "evidence_tiers": tiers, "verified_claims": len(verified),
            "direction_signal": signal,
            "direction": record.get("direction") or "direction unknown"}


def group_for(verdict: str, trial_count: int) -> str:
    """Triage group. A registered trial is a fact and outranks any verdict."""
    if trial_count > 0:
        return "already in trials"
    if verdict in ("mixed or contested", "possible wrong direction"):
        return "contested or possible wrong direction"
    if verdict == "none in the retrieved set":
        return "insufficient evidence retrieved"
    return "supported but untested"


def build(root: Path) -> dict:
    families = json.loads((root / "artifacts/family_rankings.json").read_text())
    evidence = json.loads((root / "artifacts/evidence.json").read_text())["families"]
    labels = {row["drug_id"]: row for row in
              json.loads((root / "artifacts/trial_labels.json").read_text())["labels"]}
    reviewed = [f for f in families if f["id"] in evidence]
    top_score = max((f["score"] for f in reviewed), default=1.0) or 1.0

    cards = []
    for family in reviewed:
        record = evidence[family["id"]]
        assessment = verdict_for(record)
        trials = [trial for member in family["members"]
                  for trial in labels.get(member["drug_id"], {}).get("trials", [])]
        unique_trials = list({trial["nct_id"]: trial for trial in trials}.values())
        cards.append({
            "family_id": family["id"], "family_name": family["name"],
            "rank": family["rank"], "members": [m["name"] for m in family["members"]],
            "representative_id": family["representative_id"],
            "path_score": family["score"],
            "path_strength": round(family["score"] / top_score, 4),
            "path_count": family["members"][0]["path_count"],
            **assessment,
            "trial_count": len(unique_trials),
            "trials": [{"nct_id": t["nct_id"], "title": t["title"]} for t in unique_trials],
            "retrieved_count": record["retrieval"]["retrieved_count"],
            "freshness": "cached",
            "group": group_for(assessment["verdict"], len(unique_trials)),
        })

    report = {
        "families": cards,
        "counts": {group: sum(1 for c in cards if c["group"] == group) for group in GROUPS},
        "verdict_counts": {v: sum(1 for c in cards if c["verdict"] == v) for v in VERDICTS},
        "scope": "Display-only triage for researchers. These groups are not a ranking of which "
                 "drugs work, and nothing here feeds the path ranking or the validation metrics.",
        "absence_note": "An empty or thin result means none in the retrieved set for this query, "
                        "not that no evidence exists.",
        "disclaimer": "Research hypothesis, not medical advice.",
    }
    write_json(root / "artifacts/gap_map.json", report)
    print(json.dumps({"families": len(cards), "groups": report["counts"],
                      "verdicts": report["verdict_counts"]}, indent=2))
    return report
