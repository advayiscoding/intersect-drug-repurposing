"""Quote-backed, reviewed strict labels over immutable raw ranks; no label fitting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from .data import digest, normalize, write_json
from .diseases import DISCLAIMER
from .primary_validation import evaluate_rankings

RULE_COMMIT = "c041084"
RULE_PATH = "docs/STRICT_LABEL_RULE.md"
REASONS = {"healthy_only", "interaction_probe", "pk_only", "condition_mismatch",
           "background_or_coadministered", "no_clinical_objective", "unclear_population", "unclear_role"}
MODULES = ("identificationModule", "conditionsModule", "eligibilityModule", "designModule",
           "descriptionModule", "armsInterventionsModule", "outcomesModule", "statusModule")


def field_value(protocol, path):
    value = protocol
    try:
        for key in path.split("."):
            value = value[int(key)] if isinstance(value, list) else value[key]
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise ValueError(f"Invalid evidence field: {path}") from error
    if not isinstance(value, str):
        raise ValueError("Evidence field must contain source text")
    return value


def validate_decisions(records, decisions):
    by_id = {r["record_id"]: r for r in records}
    ids = [d["record_id"] for d in decisions]
    if len(by_id) != len(records) or len(ids) != len(set(ids)) or set(ids) != set(by_id):
        raise ValueError("Exactly one decision is required for every source record")
    positives, with_uncertain = set(), set()
    for decision in decisions:
        status = decision["decision"]
        reasons = decision.get("reasons", [])
        if status not in {"include", "exclude", "uncertain"} or not set(reasons) <= REASONS:
            raise ValueError("Unknown decision or reason")
        if not decision.get("rationale", "").strip():
            raise ValueError("Every decision requires a rationale")
        evidence = decision.get("evidence", {})
        if status == "include" and (reasons or not {"population", "role", "clinical"} <= evidence.keys()):
            raise ValueError("Inclusion needs all three affirmative evidence gates and no exclusion reasons")
        if status == "include":
            fields = {
                "population": ("eligibilityModule.", "armsInterventionsModule.armGroups.", "descriptionModule."),
                "role": ("armsInterventionsModule.", "descriptionModule."),
                "clinical": ("outcomesModule.", "descriptionModule."),
            }
            for gate, allowed in fields.items():
                if not evidence[gate]["field"].startswith(allowed):
                    raise ValueError(f"Unsupported {gate} evidence field")
        if status != "include" and (not reasons or not evidence):
            raise ValueError("Excluded/uncertain records need source evidence and reason codes")
        record = by_id[decision["record_id"]]
        for item in evidence.values():
            quote = item.get("quote", "")
            if not quote.strip() or quote not in field_value(record["protocol"], item["field"]):
                raise ValueError(f"Unverified source quote in {decision['record_id']}")
        if status == "include":
            positives.add(record["drug_id"])
        if status in ("include", "uncertain"):
            with_uncertain.add(record["drug_id"])
    return positives, with_uncertain


def export_sources(root: Path):
    """Export only source records for adjudication; deliberately omit ranks/scores."""
    for disease, raw_path in (("alzheimers", "data/raw/trials.json"),
                              ("parkinsons", "data/raw/parkinsons/trials.json")):
        destination = root / "artifacts/label_audit" / f"{disease}_sources.json"
        if destination.exists():
            raise ValueError("Source bundle already exists; preserve the audit snapshot")
        labels_path = root / "artifacts/diseases" / disease / "trial_labels.json"
        labels = json.loads(labels_path.read_text())["labels"]
        snapshot = json.loads((root / raw_path).read_text())
        studies = {s["protocolSection"]["identificationModule"]["nctId"]: s["protocolSection"]
                   for s in snapshot["studies"]}
        records = {}
        for label in sorted(labels, key=lambda r: r["drug_id"]):
            for trial in sorted(label["trials"], key=lambda t: (t["nct_id"], t["intervention"])):
                nct = trial["nct_id"]
                rid = f"{label['drug_id']}:{nct}:{normalize(trial['intervention'])}"
                protocol = studies[nct]
                records[rid] = {"record_id": rid, "drug_id": label["drug_id"],
                    "drug_name": label["name"], "nct_id": nct, "intervention": trial["intervention"],
                    "matched_names": trial["matched_names"],
                    "protocol": {m: protocol[m] for m in MODULES if m in protocol}}
        write_json(destination, {"disease_id": disease, "disclaimer": DISCLAIMER,
            "rule_commit": RULE_COMMIT, "rule_sha256": digest(root / RULE_PATH),
            "snapshot_sha256": digest(root / raw_path), "raw_labels_sha256": digest(labels_path),
            "records": list(records.values())})
        print(f"Exported {disease} source records (no ranks or scores): {destination}")


def evaluate(root: Path):
    import hashlib
    committed_rule = subprocess.check_output(["git", "show", f"{RULE_COMMIT}:{RULE_PATH}"], cwd=root)
    rule_hash = hashlib.sha256(committed_rule).hexdigest()
    if digest(root / RULE_PATH) != rule_hash:
        raise ValueError("The pre-evaluation strict rule changed")
    output = root / "artifacts/audited_validation.json"
    if output.exists():
        raise ValueError("Strict results already exist; do not recompute after inspection")
    config = json.loads((root / "config/drug_families.json").read_text())
    report = {"disclaimer": DISCLAIMER, "headline_qualifier": "small test, not shown to generalize",
              "rule_commit": RULE_COMMIT, "rule_sha256": rule_hash, "diseases": {}}
    for disease in ("alzheimers", "parkinsons"):
        folder = root / "artifacts/diseases" / disease
        source_path = root / "artifacts/label_audit" / f"{disease}_sources.json"
        decisions_path = root / "artifacts/label_audit" / f"{disease}_decisions.json"
        review_path = root / "artifacts/label_audit" / f"{disease}_review.json"
        bundle = json.loads(source_path.read_text())
        decisions = json.loads(decisions_path.read_text())
        review = json.loads(review_path.read_text())
        if any(value.get("disease_id") != disease for value in (bundle, decisions, review)):
            raise ValueError("Disease identity mismatch in audit files")
        if bundle["rule_sha256"] != rule_hash or decisions["rule_sha256"] != rule_hash:
            raise ValueError("Audit rule hash mismatch")
        if (decisions["source_sha256"] != digest(source_path) or not review.get("approved")
                or review["decisions_sha256"] != digest(decisions_path)
                or review["source_sha256"] != digest(source_path) or review["rule_sha256"] != rule_hash):
            raise ValueError("Require reviewed, unchanged source-backed decisions")
        if (not review.get("reviewer") or
                sorted(review.get("reviewed_record_ids", [])) != sorted(r["record_id"] for r in bundle["records"])):
            raise ValueError("Independent review must cover every source record")
        positives, sensitivity_positives = validate_decisions(bundle["records"], decisions["decisions"])
        rows = json.loads((folder / "discovery_rankings.json").read_text())["rankings"]
        raw = json.loads((folder / "primary_validation.json").read_text())
        frozen = json.loads((folder / "frozen_inputs.json").read_text())
        if config != frozen["families"]:
            raise ValueError("Frozen family assignments changed")
        raw_ids = {r["drug_id"] for r in json.loads((folder / "trial_labels.json").read_text())["labels"]}
        if not sensitivity_positives <= raw_ids or bundle["raw_labels_sha256"] != digest(folder / "trial_labels.json"):
            raise ValueError("Strict labels must be a subset of unchanged raw labels")
        if raw["provenance"]["rankings_sha256"] != digest(folder / "discovery_rankings.json"):
            raise ValueError("Frozen rankings changed")
        label_note = ("Studied interventions in diagnosed participants under the fixed strict rule; "
                      "clinical symptom studies may qualify. Trial participation does not establish efficacy.")
        analyses = {}
        for name, ids, uncertain_handling in (
                ("strict", positives, "uncertain excluded (primary, per docs/STRICT_LABEL_PROTOCOL.md)"),
                ("strict_sensitivity", sensitivity_positives, "uncertain counted as included (sensitivity)")):
            block = evaluate_rankings(rows, ids, config)
            block.update({"positive_ids": sorted(ids), "excluded_ids": sorted(raw_ids - ids),
                "uncertain_handling": uncertain_handling,
                "sample_note": "very small sample" if block["positive_family_count"] < 30 else "small sample",
                "headline_qualifier": report["headline_qualifier"],
                "label_note": label_note, "disclaimer": DISCLAIMER})
            analyses[name] = block
        strict = analyses["strict"]
        report["diseases"][disease] = {**analyses, "raw": raw,
            "source_sha256": digest(source_path), "decisions_sha256": digest(decisions_path),
            "review_sha256": digest(review_path), "rankings_sha256": digest(folder / "discovery_rankings.json")}
    report["hard_stop"] = report["diseases"]["alzheimers"]["strict"]["heldout_count"] < 10
    write_json(output, report)
    print(json.dumps({d: {"strict_labels": v["strict"]["heldout_count"],
                         "strict_families": v["strict"]["positive_family_count"],
                         "path": v["strict"]["methods"].get("path_only")}
                      for d, v in report["diseases"].items()}, indent=2))
    if report["hard_stop"]:
        raise RuntimeError("HARD STOP: fewer than 10 Alzheimer strict labels; do not proceed to later phases")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("export-sources", "evaluate"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    (export_sources if args.command == "export-sources" else evaluate)(args.root)
