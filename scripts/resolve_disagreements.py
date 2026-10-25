"""Apply the pre-declared disagreement rule to adjudicated label decisions.

`docs/STRICT_LABEL_PROTOCOL.md` fixes this before any metric exists: where the
independent reviewer and the adjudicator disagree in either direction, the record
becomes `uncertain`, which the primary analysis excludes and the sensitivity
analysis includes. There is no third tie-breaker, because a tie-breaker chosen after
seeing the split is the failure this is meant to prevent.

This is a mechanical transformation, not a judgement: it reads both files, demotes
exactly the disagreements, records what it changed, and re-pins the decision hash
inside the review so the evaluator's integrity checks still hold.

    PYTHONPATH=src python3 scripts/resolve_disagreements.py --check   # report only
    PYTHONPATH=src python3 scripts/resolve_disagreements.py           # apply
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

DISEASES = ("alzheimers", "parkinsons")
FALLBACK_REASON = "unclear_population"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kappa(adjudicator: dict, reviewer: dict, ids: list[str]) -> dict:
    categories = ("include", "exclude", "uncertain")
    n = len(ids)
    agreed = sum(1 for r in ids if adjudicator[r] == reviewer[r])
    observed = agreed / n
    expected = sum((sum(1 for r in ids if adjudicator[r] == c) / n) *
                   (sum(1 for r in ids if reviewer[r] == c) / n) for c in categories)
    return {"records": n, "agreed": agreed, "disagreed": n - agreed,
            "observed_agreement": round(observed, 4), "expected_agreement": round(expected, 4),
            "cohens_kappa": round((observed - expected) / (1 - expected), 4) if expected < 1 else None}


def resolve(root: Path, apply: bool) -> dict:
    summary = {}
    for disease in DISEASES:
        folder = root / "artifacts/label_audit"
        decisions_path = folder / f"{disease}_decisions.json"
        review_path = folder / f"{disease}_review.json"
        source_path = folder / f"{disease}_sources.json"
        if not review_path.exists():
            summary[disease] = {"status": "no review yet"}
            continue

        decisions = json.loads(decisions_path.read_text())
        review = json.loads(review_path.read_text())
        ids = [r["record_id"] for r in json.loads(source_path.read_text())["records"]]
        by_adjudicator = {d["record_id"]: d for d in decisions["decisions"]}
        by_reviewer = {r["record_id"]: r for r in review["reviews"]}

        stats = kappa({k: v["decision"] for k, v in by_adjudicator.items()},
                      {k: v["reviewer_decision"] for k, v in by_reviewer.items()}, ids)

        changes = []
        for record_id in ids:
            adjudicated, reviewed = by_adjudicator[record_id], by_reviewer[record_id]
            if adjudicated["decision"] == reviewed["reviewer_decision"]:
                continue
            reasons = sorted(set(adjudicated.get("reasons") or []) |
                             set(reviewed.get("reasons") or []))
            changes.append({
                "record_id": record_id,
                "adjudicator_decision": adjudicated["decision"],
                "reviewer_decision": reviewed["reviewer_decision"],
                "resolved_to": "uncertain",
                "resolved_reasons": reasons or [FALLBACK_REASON],
                "reviewer_note": reviewed.get("disagreement_note", ""),
            })
            if apply:
                adjudicated["decision"] = "uncertain"
                adjudicated["reasons"] = reasons or [FALLBACK_REASON]
                adjudicated["rationale"] = (
                    f"Resolved to uncertain under docs/STRICT_LABEL_PROTOCOL.md: the independent "
                    f"reviewer read this record as '{reviewed['reviewer_decision']}' where the "
                    f"adjudicator read it as '{changes[-1]['adjudicator_decision']}'. Original "
                    f"adjudicator rationale: {adjudicated.get('rationale', '').strip()}")

        summary[disease] = {"agreement": stats, "disagreements": changes}

        if apply:
            decisions["disagreement_resolution"] = {
                "protocol": "docs/STRICT_LABEL_PROTOCOL.md",
                "rule": "reviewer disagreement in either direction becomes uncertain",
                "reviewer": review.get("reviewer"),
                "agreement": stats,
                "resolved": changes,
            }
            decisions_path.write_text(json.dumps(decisions, indent=2) + "\n")
            # Re-pin so the evaluator's hash check holds against the resolved file.
            review["decisions_sha256"] = sha256(decisions_path)
            review["resolution_applied"] = {
                "protocol": "docs/STRICT_LABEL_PROTOCOL.md",
                "records_demoted_to_uncertain": [c["record_id"] for c in changes],
                "note": "decisions_sha256 re-pinned to the post-resolution file; the reviewer's "
                        "own per-record decisions above are unchanged.",
            }
            review_path.write_text(json.dumps(review, indent=2) + "\n")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--check", action="store_true", help="report without writing")
    args = parser.parse_args()
    print(json.dumps(resolve(args.root, apply=not args.check), indent=2))


if __name__ == "__main__":
    main()
