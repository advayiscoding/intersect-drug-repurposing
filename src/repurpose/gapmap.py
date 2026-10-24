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

# Group names deliberately describe the DATASET, not the world: "no trial record
# found" is a statement about this snapshot, never a claim that a drug is untested.
GROUPS = ("already in trials", "contested or possible wrong direction",
          "evidence retrieved, no trial record found", "no evidence retrieved")


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


# A review that reports randomized-trial results is still human evidence. Only
# explicit randomized-trial phrasing counts: a bare "clinical trial" mention is
# usually about other drugs ("numerous clinical trials for AD have failed").
RANDOMIZED = ("randomized controlled trial", "randomised controlled trial",
              "randomized trial", "randomised trial", " rct", "(rct")


def claim_tier(claim: dict) -> str:
    tier = evidence_tier(claim.get("evidence_type") or "")
    if tier in ("review", "other") and any(p in (claim.get("quote") or "").casefold() for p in RANDOMIZED):
        return "human trial"
    return tier


# Disease-relevance is a DISPLAY TAG, not a verdict input. It answers "was the
# human evidence about Alzheimer's or about some other condition?", which the
# verdict rules do not look at. No verdict changes because of it.
# Alzheimer-specific disease context only, matched against the VERBATIM QUOTE and
# never the agent's own sentence. Mechanism words ("amyloid") are excluded because a
# trial in another condition mentions them in passing, and bare "dementia" is
# excluded because it spans many diseases: cerliponase alfa's records describe
# "progressive dementia in children" (CLN2), which is not Alzheimer's evidence.
ALZHEIMER_TERMS = ("alzheimer", "mild cognitive impairment", "amnestic")
RELEVANCE = {"alzheimer": "human evidence in Alzheimer's",
             "other": "human evidence in other conditions",
             "unassessed": "relevance not assessed"}


def mentions_alzheimer(claim: dict) -> bool:
    quote = (claim.get("quote") or "").casefold()
    return any(term in quote for term in ALZHEIMER_TERMS)


def disease_relevance(verified: list[dict]) -> dict:
    """Tag the human-tier evidence by the condition it was reported in."""
    human = [c for c in verified if claim_tier(c) == "human trial"]
    if not human:
        return {"key": "unassessed", "label": RELEVANCE["unassessed"],
                "human_claims": 0, "human_claims_in_alzheimer": 0,
                "note": "No verified human-trial claim, so disease relevance was not assessed."}
    in_ad = [c for c in human if mentions_alzheimer(c)]
    key = "alzheimer" if in_ad else "other"
    return {"key": key, "label": RELEVANCE[key], "human_claims": len(human),
            "human_claims_in_alzheimer": len(in_ad),
            "note": ("At least one verified human-trial claim names an Alzheimer's or dementia "
                     "context." if in_ad else
                     "Verified human-trial claims exist, but none of them names an Alzheimer's "
                     "or dementia context; the human evidence is for other conditions.")}


def supporting_quote(record: dict, verdict: str) -> dict | None:
    """The verified claim a reader should check this verdict against."""
    verified = [c for section in ("mechanism", "safety", "skeptic", "synthesis")
                for c in record.get(section, {}).get("claims", []) if c.get("verified")]
    if not verified:
        return None
    if verdict == "supported by human evidence":
        verified.sort(key=lambda c: claim_tier(c) != "human trial")
    chosen = verified[0]
    return {"quote": chosen.get("quote"), "pmid": chosen.get("pmid"),
            "evidence_type": claim_tier(chosen), "text": chosen.get("text")}


def verdict_for(record: dict) -> dict:
    """Derive the verdict from VERIFIED claims and the reported direction only.

    Order matters and is fixed: an opposing direction outranks a contested one,
    which outranks the evidence tier. Unverified claims are ignored entirely.
    """
    verified = [claim for section in ("mechanism", "safety", "skeptic", "synthesis")
                for claim in record.get(section, {}).get("claims", []) if claim.get("verified")]
    tiers = sorted({claim_tier(claim) for claim in verified})
    tier_counts = {tier: sum(1 for c in verified if claim_tier(c) == tier) for tier in tiers}
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
    return {"verdict": verdict, "evidence_tiers": tiers, "evidence_tier_counts": tier_counts,
            "disease_relevance": disease_relevance(verified),
            "verified_claims": len(verified), "direction_signal": signal,
            "supporting_quote": supporting_quote(record, verdict),
            "direction": record.get("direction") or "direction unknown"}


def group_for(verdict: str, trial_count: int) -> str:
    """Triage group. A registered trial is a fact and outranks any verdict."""
    if trial_count > 0:
        return "already in trials"
    if verdict in ("mixed or contested", "possible wrong direction"):
        return "contested or possible wrong direction"
    if verdict == "none in the retrieved set":
        return "no evidence retrieved"
    return "evidence retrieved, no trial record found"


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

    totals = {"total": 0, "verified": 0, "failed": 0}
    failures: dict[str, int] = {}
    for record in evidence.values():
        for section in ("mechanism", "safety", "skeptic", "synthesis"):
            for claim in record.get(section, {}).get("claims", []):
                totals["total"] += 1
                if claim.get("verified"):
                    totals["verified"] += 1
                else:
                    totals["failed"] += 1
                    reason = (claim.get("failure") or "unknown").split(" (")[0]
                    failures[reason] = failures.get(reason, 0) + 1

    report = {
        "families": cards,
        "verification": {
            "families_reviewed": len(evidence),
            "families_with_a_verified_claim": sum(
                1 for r in evidence.values() if r["claim_counts"]["verified"] > 0),
            "claims_generated": totals["total"],
            "claims_verified": totals["verified"],
            "claims_dropped_or_flagged": totals["failed"],
            "failure_fraction": round(totals["failed"] / totals["total"], 4) if totals["total"] else None,
            "failure_reasons": dict(sorted(failures.items(), key=lambda kv: -kv[1])),
            "method": "Span-level: the PMID must be in that family's retrieved set and the "
                      "8-40 word quote must appear verbatim in that record's title or abstract. "
                      "A flagged claim is never shown as supported.",
        },
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
                      "verdicts": report["verdict_counts"],
                      "verification": report["verification"]}, indent=2))
    return report
