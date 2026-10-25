# Rank-blind strict-label adjudication task

Read `docs/STRICT_LABEL_RULE.md` first: committed at c041084 before any strict
assignment or metric. It is immutable. Apply all three gates, do not optimize
inclusion, and never inspect ranking positions/scores or evaluate aggregate metrics.
Only two already-authorized diseases; no external requests or paid calls.

Input: `artifacts/label_audit/<disease>_sources.json`. Its records deliberately omit
ranks. Each record is a raw drug–NCT–intervention occurrence; review every record.
Read the actual population criteria, summary/objectives, experimental-arm role and
outcomes. The source audit is a starting point, not a strict decision. Missing or
ambiguous affirmative evidence fails closed. Include symptom studies in diagnosed
patients when the focal drug is studied for that clinical symptom. Distinguish
explicit disease cohorts from unseparated MCI/healthy/other-disorder mixtures.

Output only your assigned disease's `artifacts/label_audit/<disease>_decisions.json`,
plus `docs/<DISEASE>_ADJUDICATION.md` describing difficult records and assumptions.
Do not modify rule, source bundle, code, rankings, agent/verdict logic, context or
other files. Parent commits the phase. Use apply_patch for editing; a temporary
curated generator in /tmp is permitted for generating the JSON from explicit
per-record selections, but do not create new automated eligibility heuristics.

JSON schema:

```json
{
  "disease_id": "assigned disease",
  "rule_sha256": "SHA256 of docs/STRICT_LABEL_RULE.md",
  "source_sha256": "SHA256 of source bundle",
  "disclaimer": "Research hypothesis, not medical advice. This tool does not tell anyone what to take. Talk to a doctor or pharmacist about any medicine.",
  "decisions": [{
    "record_id": "exact source record_id",
    "decision": "include or exclude or uncertain",
    "reasons": [],
    "rationale": "Source-specific clinical/role explanation, never a ranking claim",
    "evidence": {
      "population": {"field": "eligibilityModule.eligibilityCriteria", "quote": "verbatim source span"},
      "role": {"field": "descriptionModule.briefSummary", "quote": "verbatim source span"},
      "clinical": {"field": "outcomesModule.primaryOutcomes.0.measure", "quote": "verbatim source span"}
    }
  }]
}
```

`field` is a dot path relative to the record's `protocol`; list indexes are numeric.
All quote text must be an exact, nonempty substring of that string field (preserve
apostrophes/Unicode). Inclusion requires population, role and clinical evidence
and no reason codes. Exclusion/uncertain needs at least one evidence span and a
nonempty reason list from: healthy_only, interaction_probe, pk_only,
condition_mismatch, background_or_coadministered, no_clinical_objective,
unclear_population, unclear_role. Multiple reasons can apply. Each source record
must have exactly one decision, no duplicates or extras. For exclusion the evidence
keys may be arbitrary descriptive names. Do not use absence alone as an assertion
of a definitive exclusion; uncertainty is an available outcome.

Validate quote paths/coverage with `repurpose.strict_labels.validate_decisions`
but do not print its returned positive set or compute ranking results. Review
the reasoning yourself before sending to independent reviewer. Report status,
files, validation pass/fail and difficult cases, not performance numbers. Parent
will have a separate reviewer check the complete decision set before metrics.
