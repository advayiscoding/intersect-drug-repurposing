# Strict-label evaluation pre-declaration

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

**Committed before any strict metric is computed.** It fixes how adjudication output
is turned into a label set, so the handling of ambiguity cannot be chosen after
seeing which choice flatters the ranking. It adds nothing to and changes nothing in
`docs/STRICT_LABEL_RULE.md` (frozen at `c041084`, rule hash
`c67af905bdf8286f22cf7c8df20a631f317cc2666836e78af924cb30b47ae2cd`), which remains
the only authority on what a record means.

## 1. How "uncertain" decisions are handled

Each adjudicated record carries `include`, `exclude` or `uncertain`. A drug is a
strict label if at least one of its raw records qualifies, per the frozen rule.

| Analysis | Treatment of `uncertain` | Status |
| --- | --- | --- |
| **Primary** | Excluded from the strict label set | The headline strict number |
| **Sensitivity** | Counted as included | Reported beside it, never instead of it |

Both are reported every time strict results are reported. The primary analysis is
the conservative one and matches the frozen rule's "uncertain never counts as a
positive" and "missing evidence fails closed". The sensitivity analysis exists so a
reader can see how much the conclusion rests on the ambiguous records; if the two
diverge materially, that divergence is the finding and must be stated as such.

Raw labels are reported alongside both. The raw set is unchanged and immutable: this
protocol only ever *removes* drugs from consideration as positives, never adds any.

## 2. How reviewer disagreements are resolved

An independent reviewer re-decides every record from the frozen rule and the
rank-free source bundle alone, without ranks, scores or metrics.

- Adjudicator and reviewer **agree** → that decision stands.
- Adjudicator and reviewer **disagree**, in any direction → the record becomes
  **`uncertain`**, and is then handled by the table above.

Disagreement therefore never resolves to the more favourable reading, and an
`include` contested by the reviewer cannot enter the primary strict set. No third
tie-breaker adjudicates, because a tie-breaker chosen after seeing the split is the
exact failure mode this pre-declaration exists to prevent.

Factual transcription errors — a quoted span that does not appear in the cited
registry field, a mis-keyed NCT id, a reason code naming a field the record does not
have — may be corrected before metrics, as the frozen rule allows. A corrected record
is re-decided under the same rule, and the correction is logged in the review report.
A change of judgement is **not** a transcription error.

## 3. What is reported

For each disease, every strict report carries, side by side:

1. **Raw** labels (unchanged, as already published),
2. **Strict primary** (uncertain excluded),
3. **Strict sensitivity** (uncertain included),

each with recall@10/20 as primary metrics, recall@50/100 secondary, exact 95%
Clopper–Pearson intervals, family-level recovery, the family permutation test, and
the all-label mean reciprocal rank reported separately from single-query MRR.
Rankings, universes, controls, family assignments, path constants and leakage guards
are untouched; only the label set differs.

Per-disease reviewer agreement counts and Cohen's kappa are reported with the
results, and every disagreement is listed with its resolution.

## 4. Sample-size labelling

Fewer than 30 positive families for a disease, or a strict set materially smaller
than its raw set, is labelled **very small sample** everywhere it appears — README,
docs, dashboard, Q&A and plain-language text alike. Every headline keeps
**small test, not shown to generalize**. Zero-label results have no defined recall
or binomial interval and are reported as undefined, not as zero.

## 5. Hard stop

Fewer than 10 Alzheimer strict labels, or any failure to establish
label-to-source provenance or fixed-ranking integrity, stops the work: report and
do not proceed to later UI or deployment phases. This pre-declaration does not
weaken that stop, and the primary analysis is the one it is evaluated against.
