# Three-minute demo

Before presenting: install/build once, run with `REPURPOSE_OFFLINE=1`, verify the
health endpoint says live agents are unavailable. Keep the tab open. No live API
calls are needed; no public deployment is required.

1. **0:00–0:25 — The intersection.** “This connects biological mechanisms, trial
   registrations and literature into an auditable hypothesis workbench, not a
   treatment recommender.” Show the family-collapsed Explore list.
2. **0:25–1:05 — Inspect one path.** Open mecamylamine. Select a scored path and
   inspect a gene/edge. Dashed pathway branches provide context, not score. Graph
   edges are unsigned: direction unknown. Open Literature review; show a verified
   PMID and supporting quote. The antagonist blocked nicotine's benefit in the
   retrieved animal work—a useful objection the graph score cannot see.
3. **1:05–1:35 — Check a hypothesis.** In Check my idea, try metformin, then
   donepezil. Metformin illustrates a cached lookup; donepezil illustrates an
   excluded known control, not a discovery or a miss. If a synonym is ambiguous,
   show the explicit choice rather than silently picking a variant.
4. **1:35–2:30 — Be honest about validation.** Lead with the **strict primary**
   result: **1 of 24 labels at 10/20, 4.17%, exact CI 0.11–21.12%**, family-aware
   permutation p@20 = 0.233, very small sample. Then say what it replaced — the raw,
   unaudited set gave 4/44 (9.09%) and p@20 = 0.080, and auditing the trial records
   against a rule frozen beforehand removed most of it. Say plainly what survives:
   **one insulin**. Insulin glulisine is the only strict top-20 hit; insulin aspart
   and detemir became uncertain on ambiguous population evidence; choline was
   excluded. Then show the embedding negative finding.
5. **2:30–3:00 — Close.** Gap map shows what is and is not in the retrieved set.
   “The value is inspectable connections and explicit objections. Trial participation
   is not efficacy, and this small retrospective evaluation does not establish
   clinical usefulness.”

## Q&A cheat sheet

- **Did you find a treatment?** No. These are ranked research hypotheses and
  retrospective recovery of trial-tested drugs, not efficacy predictions.
- **What prevents leakage?** All direct Alzheimer/drug edges, including reverses
  and every relation type, are removed before neighborhood selection, degree
  normalization and embedding training. Negatives exclude all Alzheimer/drug pairs.
  Indirect historical information can remain; this is not a temporal test.
- **Did you tune on the reported set?** Path parameters were fixed before validation.
  Embedding mixture weights used 22 tuning drugs, then 22 held-out drugs; zero
  embedding weight won. All-44 path results are retrospective descriptive results
  after method selection, not new independent confirmation.
- **Is 8× lift convincing?** It is lift against a low random baseline in a small,
  correlated sample. Only two families recover; exact drug intervals do not remove
  family dependence. The primary family permutation p-value is 0.080.
- **Can the LLM hallucinate?** Yes. The deterministic checker rejects citations
  outside the retrieved set and unmatched quotes. A matching quote does not prove
  the interpretation; unsupported summaries and heuristic verdicts need review.
- **How many papers?** The retriever requests up to eight relevant PubMed records
  per family. Absence means none in that retrieved set, not no evidence anywhere.
- **What failed?** Fixed DistMult did not improve primary recall. The graph cannot
  infer activation/inhibition, brain exposure or clinical benefit. LINCS was not added.
- **Does the demo need keys or internet?** After dependencies and frontend are built,
  no. Shipped artifacts cover all pages. Source links and optional live reviews need
  internet; offline mode prevents agent spending.
- **What would validate this next?** Independent prospective or time-split evaluation
  with broader family diversity and expert mechanism review—not stronger claims
  from the same small sample.

## Release checklist

- Run tests and production frontend build; check all four pages and narrow layout.
- Confirm portable smoke test passes without `.env`, raw data or processed graph.
- Keep live mode disabled for an unattended demo; never ship secrets or counters.
- Commit verified source/artifacts before creating a release tag. Public deployment
  requires a chosen host and explicit authorization; none is configured here.
