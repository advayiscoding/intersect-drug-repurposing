# Handoff

Alzheimer's drug-repurposing workbench on PrimeKG. Ranked repurposing candidates with
explainable graph paths, literature agents whose every claim is span-verified, an
honest validation dashboard, an evidence gap map, and a "check my idea" lookup.

**Everything here is a research hypothesis, never medical advice.** No number in this
repository is evidence of efficacy. Keep it that way.

Updated 2026-10-25. Workspace `/Users/advay/Downloads/Hackathon`, branch `feat/parkinsons-pilot`.

## Active continuation — read before the historical state below

LATEST REQUEST: final-demo phases 0–5, authorized to proceed without the old
checkpoint approvals; only the latest attachment's hard stops apply. Read
docs/FINAL_PLAN.md. Phase 0 verified 144 collected/144 passed, clean branch
feat/parkinsons-pilot at 293e85e, demo-safe/main d35abee, expected artifacts.
Secret scan: 250 reachable blobs / 164 tracked files, two configured-value checks
plus provider/private-key patterns; zero findings, no values printed. Gitleaks
not installed. Historical 132-test sections below describe the old baseline only.
Phase 0 committed as 68b10fb. Phase 1a raw audit complete: 10 labels/disease
sampled by drug ID, all 83 raw labels audited. Clear all-supporting concerns:
AD 4/44, PD 10/39; mixed/unclear AD19, PD7. See docs/LABEL_AUDIT.md.
docs/STRICT_LABEL_RULE.md is being frozen in the Phase 1a commit BEFORE assigning
strict inclusion decisions or metrics. No strict results computed. Reviewer
strict_rule_review checked the rule without accessing labels/ranks; wording clarified
separable registered contrasts and retrospective status. Parent owns evaluation;
raw_label_audit produced only the audit. Next: source bundle, rank-blind per-record
strict decisions, independent review, then fixed-rank strict/raw evaluation.
tests/test_strict_labels.py currently contains six expected failing tests for the
not-yet-created strict-label module (red phase); do not mistake this for a baseline
regression. Commit only the rule/audit/docs for the pre-evaluation freeze.
UPDATE: strict rule freeze is c041084. strict_labels.py added; six tests now pass
after observed red failures. Rank-free source bundles exported to artifacts/label_audit.
Rule hash c67af905bdf8286f22cf7c8df20a631f317cc2666836e78af924cb30b47ae2cd.
Next: quote-backed per-record adjudication and independent review using
docs/STRICT_ADJUDICATION_BRIEF.md. No strict metrics yet. The evaluator refuses
unreviewed decisions, hash changes, changed ranks, or result overwrite and raises
the hard stop if Alzheimer strict count is below 10. No UI changes yet.
Adjudicators ad_strict_decisions and pd_strict_decisions are writing separate
decision files/docs from rank-free source bundles; do not evaluate until their
independent review JSON files cover every record and pin source/rule/decision hashes.
Validator now also rejects condition/title-only inclusion evidence for population.
No new disease selectors, agents, verdict changes or paid calls. Merge to main and
demo-final tag only after all final checks. Keep demo-safe untouched.

The following Stage 1 checkpoint is historical, not the current stop instruction:

User authorized a staged multi-disease extension via attached spec. Work ONLY on
Stage 1: disease parameterization + Parkinson pilot, then STOP for user decision.
Stage 2 (ALS/Huntington/MS), Stage 3 product/evidence, and Stage 4 plain-language
layer are not authorized to proceed past this checkpoint yet. Read
docs/PARKINSONS_PLAN.md. Start time: 2026-10-24 23:59 UTC, three-hour ceiling.
Baseline: 132 tests pass; original commit d35abee; demo-safe was absent and now pins
that verified commit. Never move it. Original artifacts and web UI remain frozen.
Stage 1 COMPLETE; STOP here pending the user's decision. See
docs/PARKINSONS_CHECKPOINT.md for the result, caveats and reproducibility commands.
New outputs are under artifacts/diseases/<slug>; no product/evidence changes yet.

Verification: 144 tests pass; frontend production build passes. Existing warnings
are Starlette/httpx deprecation and Vite's large main chunk. No paid model calls.
Both real runs completed in ~22 seconds each. Parkinson: 1,774 drugs / 1,763
families; 39 labels / 39 families; path 0/39 at k=10/20 versus popularity 1/39.
Full Alzheimer replay preserves every path rank, score and degree. Final audit
found inherited registry labels include healthy-volunteer interaction probes:
acetaminophen top-50 path hit (NCT02305017), caffeine popularity hit (NCT03970798).
Keep the frozen labels/method; qualify their meaning prominently, not disease-
patient testing. Only descriptive label metadata corrected; no numbers changed.
Read-only review confirms actual saved Parkinson training edges contain zero
guarded pairs. Review gap fixed: explicit Parkinson-only guard override now fails;
only explicit Alzheimer snapshot replay may omit the cross-disease union.
Cached report: artifacts/diseases/parkinsons/report.html. Two browser-verified
screenshots: artifacts/screenshots/parkinsons-stage1.png and
parkinsons-stage1-caveats.png. Stage commit is the branch tip above d35abee.
Production changes are confined to data.py, cli.py, primary_validation.py and two
new config/runner modules plus a checkpoint renderer; scoring and UI are untouched.
Trial fetch succeeded with network approval: 2,922 records / 3 pages, 2026-10-25.
Timing: initial setup at 00:00 UTC, then a several-hour gap before the user's
“continue”; implementation files began at 04:49 UTC. Count active work separately
from that gap; do not claim the entire wall-clock interval as implementation time.
Resumed implementation/review took roughly 15 minutes, plus initial setup.
Path exact CI at 10/20: [0, 9.03]%; random expectations 0.56/1.13%; popularity 2.56%.
Family recovery among top-10/20/50 drugs: 0/0/4; collapsed-family permutation p@20
0.356 (one label in the first 20 family cards, a different unit). Secondary path
recall@50/100: 4/39 and 6/39. No tuning or favorable-result selection permitted.
Next decision is whether to proceed to Stage 2; do not infer approval from these
handoff notes. The historical "Next" section below predates this authorized pilot.

---

## 1. Read this first: the honest summary

If you demo this, these are the facts you must not soften.

- **The headline is the STRICT result: 1 of 24 Alzheimer labels at k=10/20 (4.17%),
  exact CI [0.11%, 21.12%], family permutation p@20 = 0.233.** Very small sample.
  The sensitivity analysis (uncertain counted as included) gives 3/32 = 9.38%,
  p@20 = 0.287. The raw, unaudited set gave 4/44 = 9.09%, p@20 = 0.080, and is now
  reported as secondary only.
- **Under audit the recovery is literally one insulin.** Insulin glulisine (rank 6)
  survives; insulin aspart (rank 5) and insulin detemir (rank 9) became *uncertain*
  on ambiguous population evidence; choline (rank 10) was excluded outright. The old
  "essentially insulin" caveat turned out to understate it.
- **Parkinson's is negative on both label sets.** 0/39 raw and 0/24 strict at k=10/20.
- **The embedding experiment failed.** Fixed DistMult scored 0/22 recall@10/20 on the
  reserved split; tuning selected zero embedding weight. Documented, not hidden.
- **Path scoring cannot see direction.** PrimeKG edges are undirected and unsigned.
  The #1 candidate, **mecamylamine, is a nicotinic antagonist** that *blocked*
  nicotine's cognitive benefit in the retrieved animal work. The agents caught what the
  ranking could not.
- **Verdicts are keyword heuristics**, self-audited on the same 20 families they were
  tuned on. 16/20 agree; the 4 that do not are listed in docs/METHODOLOGY.md.
- **Trial participation is not efficacy**, and absence is always "none in the retrieved
  set", never "no evidence exists".

## 2. Current state

Stages 1-5 complete, plus UI, agents, gap map and check-my-idea. Local demo
hardening is complete. **132 tests pass**, including in a clean Git-index export
without .env or ignored datasets. Python tests reused the installed runtime;
frontend dependencies were freshly installed from npm's offline cache, then built.
The inherited 187-test claim was stale; nine fixture failures are now repaired.

Test-count forensics (pytest --collect-only, verified 2026-10-25): f1abde1 collected
**106**; HEAD c041084 collects **144** committed plus 8 uncommitted strict-label tests
= 152 in the working tree. `git diff --stat f1abde1 HEAD -- tests/` is +487/-3 across
four files, with **zero test files deleted and zero test functions removed** (checked
with --diff-filter=D and a grep for removed `def test_`). No coverage was lost, so
nothing needed restoring. The "187" was an arithmetic error in a chat summary: a
full-suite run of 113 was added to a two-file run of 74 from the same session. Trust
`--collect-only`, never a remembered total.

| Commit | What |
| --- | --- |
| 874cde3 | Stage 1: leakage-safe PrimeKG Alzheimer path rankings |
| 9b19251 | Stage 2: retrospective validation vs independent trials |
| 8544c49 | Frozen controls and evaluation protocol |
| 8f44ea1 | Stage 5: DistMult evaluated, negative result retained |
| 72f1809 | All-44 primary evaluation, exact CIs, drug families |
| 4d43626 | Stage 3: workbench UI over cached artifacts |
| 4746b8b | Per-entity external node links |
| b9871af | Graph readability (dagre, label halos, path limiting) |
| 840743a | Stage 4: evidence agents + span-level citation checker |
| 8f1aed1 | Evidence gap map |
| f1abde1 | Check my idea |

**Completed in the demo-hardening commit:** inherited synonym map (PubChem),
ambiguous-synonym chooser, disease-relevance tag, pre-computed check cache, daily
cost cap, portable offline mode, regression tests and concise documentation.

Hardening continuation: frontend production build passes (large-bundle warning).
Added regression tests for portable drug lookup, explicit offline mode, budget
endpoint coverage, corrupt-counter fail-closed behavior, and concurrent consumers.
The old counter allowed 94/100 concurrent requests with a limit of five. Now uses
a POSIX file lock and atomic replacement, shared across threads/processes on the
same disk; day boundary is UTC. Both live API routes share one guarded runner.
Unknown/ambiguous lookups no longer consume an agent budget. No paid API calls.
`build-check-cache` now exports artifacts/drug_index.json from the full graph drug
vocabulary, removing the demo's dependency on ignored processed nodes.
Cache regenerated: 28 common queries, 22 with cached paths. Portable API smoke test
passes using copied source/artifacts/synonyms, no .env/raw/processed files and HTTP
blocked. Full suite: 132 passed after final review adjustments. README is now
short; full method/audit history moved to docs/METHODOLOGY.md, demo/Q&A docs/DEMO.md.
Browser review caught a misleading control header (“no path”); now states known
control excluded from discovery, not biological absence. Review also added strict
counter-date validation and shared frontend session ID across both live routes.
Review findings fixed: counter dates validated, both frontend live routes share
the session ID, quota metadata preserved. All four pages were checked in the
browser at narrow width; graph selection, cached literature, known-control lookup,
metformin lookup and validation numbers work. Final screenshots are in
artifacts/screenshots/demo-{graph,known-control,validation}.png.
Nonblocking warnings: Vite's ~714 kB main chunk, Starlette/httpx deprecation.
No paid/provider calls, no model retraining and no public deployment this turn.
Clean export tested at /tmp/intersect-demo-export.cluHoK (disposable, no secrets).

## 3. How to run it

```sh
python -m pip install -e '.[test,demo]'
npm ci --prefix web
npm run build --prefix web
REPURPOSE_OFFLINE=1 PYTHONPATH=src python3 -m uvicorn repurpose.api:app --app-dir src --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. Four pages: **Explore** (candidate families, graph paths,
evidence), **Gap map** (triage), **Check my idea** (arbitrary drug), **Validation**
(the honest dashboard). It runs from artifacts plus data/synonyms.json with no keys
or external requests. Source links need internet if clicked. Installation/build
needs package downloads or a populated package cache, not the raw biological data.

Rebuild commands (all optional, all offline except the two marked):

```sh
PYTHONPATH=src python3 -m repurpose.cli validate           # split metrics
PYTHONPATH=src python3 -m repurpose.cli validate-primary   # all-44 primary report
PYTHONPATH=src python3 -m repurpose.cli prepare-ui         # explorer_details.json
PYTHONPATH=src python3 -m repurpose.cli build-gap-map      # gap_map.json
PYTHONPATH=src python3 -m repurpose.cli build-check-cache  # check_cache.json
PYTHONPATH=src python3 -m repurpose.cli build-synonyms     # NETWORK: PubChem
PYTHONPATH=src python3 -m repurpose.cli build-evidence     # NETWORK + LLM: costs money
```

`cd web && npm install && npm run build` rebuilds the frontend into `web/dist`.

## 4. Architecture

```
PrimeKG CSV ──▶ graph.py ──▶ training_edges.parquet ──▶ ranking.py ──▶ rankings
  (937 MiB)     leakage        (sanitized, the only      (fixed path     (frozen)
                removal         allowed model input)      scoring)
                                                              │
CT.gov ──▶ data.py ──▶ trial_labels.json ──▶ primary_validation.py ──▶ metrics
                                                              │
                                        families.py ──▶ family_rankings.json
                                                              │
PubMed ──▶ pubmed.py ──▶ agents.py ──▶ citations.py ──▶ evidence.json
          (cached)      (5 roles)     (span check)         │
                                                    gapmap.py ──▶ gap_map.json
                                                              │
                                        api.py (read-only) ──▶ web/ (React+Cytoscape)
```

Everything the UI shows is a cached artifact. The API computes nothing per request
except an optional live agent run.

## 5. Invariants — do not break these

1. **Leakage.** `remove_target_drug_edges` strips every target-drug edge in both
   orientations and all relation types, for **all** drugs, before neighborhood
   selection and degree computation. The negative sampler rejects every target/drug
   pair in either direction. Tests: `tests/test_leakage.py`, `tests/test_embeddings.py`.
2. **No tuning on the test set.** The 22/22 split experiment is frozen in
   `split_validation.json`. Training and tuning commands refuse to overwrite a fitted
   experiment. Do not regenerate the split.
3. **Agent output never feeds the ranking or validation.** It is display-only, and the
   dashboard says so.
4. **Nothing unverified is shown as supported.** Every claim needs a PMID in that
   family's retrieved set plus an 8-40 word verbatim quote. Failures are flagged.
5. **User text only ever looks up a node.** Agent prompts and PubMed queries receive
   the canonical graph name, never raw input.
6. **API keys are server-side only.** A test asserts no endpoint returns key material.

## 6. Key numbers

| Thing | Value |
| --- | ---: |
| Discovery pool | 1,792 drugs / 1,781 families |
| Trial labels | 44 (9 controls excluded) / 41 positive families |
| Alzheimer strict primary recall@10/20 | 4.17% (1/24), exact CI [0.11, 21.12]% |
| Alzheimer strict sensitivity | 9.38% (3/32), exact CI [1.98, 25.02]% |
| Alzheimer raw, secondary | 9.09% (4/44), exact CI [2.53, 21.67]%, enrichment@20 8.15x |
| Distinct families recovered, strict | 1 of 23 (insulin glulisine) |
| Family permutation p@20 | 0.233 strict / 0.287 sensitivity / 0.080 raw |
| Parkinson strict / raw recall@10/20 | 0/24 and 0/39 |
| Reviewer agreement (AD / PD) | kappa 0.856 / 0.961 |
| Agent families cached | 20 |
| Families with >=1 verified claim | 17 |
| Claims generated / verified / failed | 231 / 229 / 2 (0.87%) |
| Gap map groups | 12 evidence-no-trial, 2 in trials, 3 contested, 3 no evidence |
| Disease relevance | 3 Alzheimer's, 7 other conditions, 10 not assessed |

## 7. Traps and hard-won lessons

Read these before touching the relevant code; each one cost real debugging.

- **`build_graph` once stored edge provenance under the key `source`**, which
  `ranking.py` spread over the path edge's `source` endpoint, so every cached path edge
  read `"source": "PrimeKG"` instead of a node id. It is now `provenance`.
- **"inhibit" is NOT an opposing direction.** An MAO inhibitor inhibits by design.
- **A harm noun alone is not harm.** "Reducing behavioural deficits" is protective, so
  an opposing reading needs a harm verb AND a harm noun with no protective word.
- **Do not feed safety/skeptic text into the direction classifier.** I implemented and
  tested it: it flipped five families to "possible wrong direction" because skeptic
  claims routinely mention impairment when describing the disease. Rejected.
- **Disease relevance must match the verbatim quote, not the agent's sentence**, and
  bare "dementia" must not count: cerliponase alfa's records say "progressive dementia
  in children" (CLN2), and its skeptic wrote "not adults with Alzheimer's".
- **A bare "clinical trial" mention does not imply human evidence for this drug** —
  "numerous clinical trials for AD have failed" is about other drugs. Only explicit
  randomized-trial phrasing promotes a review to human-tier.
- **Sonnet does not support assistant prefill**, and agent calls need ~8000 max_tokens
  or they truncate mid-JSON.
- **html2canvas cannot capture the Cytoscape canvas** unless the browser pane is
  FRONTED and the render is first baked into an `<img>` via `cy.png()`.
- **`api.py` uses `lru_cache` on artifacts**, so restart the server after rebuilding
  any artifact or you will serve stale JSON.
- **PubChem is latency-bound, not rate-bound.** 16 workers behind a shared 5/s token
  bucket; a serial loop takes two hours.

## 8. Costs and credentials

`.env` is Git-ignored and has **never** been committed — verified by scanning every
commit for both key values and for any `sk-ant-` literal; `.env` appears in no commit.
Keys: `ANTHROPIC_API_KEY` (agents, claude-sonnet-5), `NCBI_API_KEY` (PubMed throughput).

The user has limited credits. **Be sparing.** `build-evidence` costs roughly 4 LLM
calls per family; use `--family` to scope reruns and never pass `--refresh` casually.
Three cost brakes, in order of trustworthiness: a provider-side hard spend limit (the
only one a restart cannot defeat), a persisted daily cap (`REPURPOSE_DAILY_LIVE_CAP`,
default 40 — **resets on ephemeral-disk hosts**), and a 5-per-10-minutes session limit.

## 9. Where things live

`src/repurpose/`: `data.py` (sources, CT.gov) · `graph.py` (leakage removal, graph) ·
`ranking.py` (fixed path scoring) · `protocol.py` (frozen split) · `evaluation.py` ·
`primary_validation.py` (all-44, exact CIs, permutation) · `validation.py` (split) ·
`embeddings.py` (DistMult, negative result) · `selection.py` · `families.py` ·
`links.py` (per-entity URLs) · `ui_data.py` · `pubmed.py` · `agents.py` (5 roles) ·
`citations.py` (span checker) · `evidence.py` · `gapmap.py` (verdicts, relevance) ·
`resolve.py` (sanitize, drug index) · `synonyms.py` (PubChem) · `check.py` ·
`check_cache.py` · `ratelimit.py` · `api.py` · `cli.py`

`artifacts/` is the UI's whole world; `artifacts/screenshots/` holds before/after
images. `scripts/label_overlap_audit.js` measures caption collisions in the live page.
`ASSUMPTIONS.md` records judgement calls. `README.md` is the short quickstart;
`docs/METHODOLOGY.md` holds the full methodology and `docs/DEMO.md` the demo/Q&A.

## 10. Next

Local demo is ready. Rehearse docs/DEMO.md (about 10–15 minutes). Public deployment
has not been performed: obtain the user's chosen/approved host before exposing the
app, deploy offline by default, and never ship .env or runtime budget counters.
Allow roughly 30–60 minutes for hosting setup and smoke checks once a target exists.
Do not start a Parkinson's pilot without a new user request; it is outside the
approved Alzheimer's scope. No additional embedding work is needed.
