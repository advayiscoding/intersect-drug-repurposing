# Strict trial-label protocol v1 — freeze before evaluation

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

## Purpose and pre-evaluation freeze

This rule tests recovery of drugs studied as interventions in participants with
the selected disease, not mere occurrence in a disease-tagged registry record.
It is identical for Alzheimer and Parkinson apart from the disease identity.
It must be committed before assigning strict inclusion decisions or computing
strict metrics. The prior raw result is already known; this is a transparent
protocol correction, not a new untouched prospective test. No result-dependent
revision is permitted. Rankings, candidate universes, controls, family assignments,
path constants and leakage guards remain unchanged.

## Gate 1: retain every raw eligibility requirement

1. Use the existing dated CT.gov snapshots and disease condition matcher.
2. Study type INTERVENTIONAL; status COMPLETED or TERMINATED.
3. Primary purpose TREATMENT; ACTUAL enrollment greater than zero.
4. Intervention type DRUG, linked to an EXPERIMENTAL arm.
5. A primary name or registered `otherNames` value normalizes to exactly one
   PrimeKG drug identity; no new synonyms, fuzzy matches or combination splitting.
6. Drug belongs to the frozen non-target-indication candidate universe and is
   not a known control. No new positives outside the original raw label set.

## Gate 2: affirmative disease-participant evidence

Registry inclusion criteria or an explicit cohort/arm description must require
the target disease in participants receiving the labeled intervention. A condition
tag, the title alone, or `healthyVolunteers=false` alone is insufficient.

- Alzheimer: an explicit clinical diagnosis of Alzheimer disease/dementia,
  probable/possible Alzheimer disease, or explicitly biomarker-supported prodromal
  Alzheimer disease. Mild cognitive impairment or cognitive decline alone does
  not qualify. A prevention study in unaffected at-risk participants does not qualify.
- Parkinson: an explicit clinical diagnosis of Parkinson disease, including
  idiopathic Parkinson disease. Generic parkinsonism, another movement disorder,
  or drug-induced parkinsonism alone does not qualify.
- Healthy-only records are excluded. Mixed cohorts qualify only if a separately
  identifiable disease cohort receives the labeled intervention and its clinical
  outcomes are separately specified. Otherwise mark uncertain and exclude.
- Clinical symptom studies in diagnosed participants may qualify; disease
  modification is not required. This scope is stated with every interpretation.

## Gate 3: the drug is the studied intervention, not background/probe

The objective/summary plus arms/interventions must affirmatively identify the
labeled drug as the intervention under evaluation for a clinical outcome in that
disease cohort. Clinical outcomes include symptoms, functioning, cognition and
quality of life. Clinical secondary outcomes count if the objective explicitly
studies the drug's clinical effects; an incidental clinical measure does not.

Exclude drugs used only as index substrates, interaction probes, challenge agents,
tracers, procedural sedation, rescue medication or stable/background co-medication.
A drug listed in an experimental arm is not enough. For multi-drug regimens, include
a component only if an explicit component-specific randomized/factorial or otherwise
separable clinical contrast, specified in registered arms/cohorts and objectives,
studies that component. Otherwise exclude as co-administered
or mark uncertain. A drug deliberately varied against stable background therapy
can qualify; the unchanged background drug cannot.

Exclude PK/bioavailability/bioequivalence/drug-interaction-only studies and studies
limited to tolerability, safety, imaging or laboratory biomarkers without a
disease-relevant clinical objective/outcome. Phase number alone neither includes
nor excludes a study. Do not infer role or purpose from the observed ranking.

## Adjudication and reproducibility

Review every raw drug–trial–intervention record in ascending drug ID and NCT order,
without ranking scores or positions. Assign include / exclude / uncertain and
reason codes: healthy_only, interaction_probe, pk_only, condition_mismatch,
background_or_coadministered, no_clinical_objective, unclear_population,
unclear_role. Categories may overlap; uncertain never counts as a positive.

Each inclusion must preserve verbatim registry spans establishing (1) disease
population, (2) focal intervention role, and (3) clinical objective/outcome, with
field identifiers. Exclusions/uncertainties preserve their supporting spans and
rationale too. An independent reviewer, without ranks or scores, checks these
judgments against the same rule and records disagreements. Factual transcription/application errors may be corrected before metrics,
but the rule cannot change after results. Missing evidence fails closed.

A drug is a strict label if at least one of its original raw records satisfies
all gates. Multiple studies or related variants do not create extra labels.
Record source snapshot, rule and decision-file hashes. Keep original raw artifacts
immutable, with strict and raw reports in a new comparison artifact.

## Evaluation and hard stop

Use the existing fixed path ranks, popularity ranks and random baseline, exact
95% Clopper–Pearson intervals, family recovery and family permutation test.
Recall@10/20 remain primary. Do not optimize any weight, rule, threshold or filter.
Report all-label mean reciprocal rank separately from single-query MRR.

Fewer than 30 positive families per disease: label numbers **very small sample**
and keep exact intervals. Fewer than 10 Alzheimer strict labels, or inability to
establish label-to-source provenance or fixed-ranking integrity: stop and report,
without completing later UI
or deployment phases. Zero-label results have no defined recall or binomial CI.

Every headline is qualified **small test, not shown to generalize**. Trial
participation does not establish efficacy. These labels include clinical symptom
studies and do not establish disease modification or a recommendation.
