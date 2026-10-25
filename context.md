# Handoff

Alzheimer's drug-repurposing workbench on PrimeKG. Ranked repurposing candidates with
explainable graph paths, literature agents whose every claim is span-verified, an
honest validation dashboard, an evidence gap map, and a "check my idea" lookup.

**Everything here is a research hypothesis, never medical advice.** No number in this
repository is evidence of efficacy. Keep it that way.

Updated 2026-10-25. Workspace `/Users/advay/Downloads/Hackathon`, branch `main` at tag `demo-final`.

## Where this left off

**All phases complete.** `main` is at the `demo-final` tag; `demo-safe` is untouched
at `d35abee`. 191 tests pass, frontend builds, fresh clone verified offline with no
keys, and a production server was verified serving the tag itself.

Phase ledger (docs/FINAL_PLAN.md) is fully checked: 0 baseline, 1a rule freeze,
1b strict evaluation, 2 Parkinson static table, 3 plain-language mode, 4 fresh clone
and deployment prep, 5 final checks and tag.

What the strict audit did to the headline:

| Alzheimer's | Labels | Hits@10/20 | Recall | Exact CI | Families | p@20 |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| Strict (primary) | 24 | 1 | 4.17% | 0.11-21.12% | 1 of 23 | 0.233 |
| Strict sensitivity | 32 | 3 | 9.38% | 1.98-25.02% | 1 of 29 | 0.287 |
| Raw (secondary) | 44 | 4 | 9.09% | 2.53-21.67% | 2 of 41 | 0.080 |

Parkinson's: 0 of 24 strict, 0 of 39 raw. Reviewer agreement kappa 0.856 (AD) and
0.961 (PD); six disagreements all demoted to uncertain by the pre-declared rule.

**Open items for whoever picks this up:**

1. `demo-safe` was NOT moved. The last instruction said to tag the hardened commit
   `demo-safe`, but that tag already pinned d35abee under a standing "never move it",
   so `demo-final` was created instead and the conflict was reported twice without a
   reply. Moving it is a one-line change if that is what was wanted.
2. **No public deployment happened.** FINAL_PLAN forbids exposing the service in this
   task and no hosting credentials were used. Dockerfile and docs/DEPLOYMENT.md are
   ready; the pre-flight list starts with a provider-side spend limit.
3. A cross-contamination incident: two blinded reviewers run concurrently returned
   each other's shell output once. Review data was verified clean, but **never run
   two blinded agents in parallel with a shared scratch namespace.**
4. The `no_clinical_objective` threshold lands inconsistently across four label
   records. Deliberately not fixed, because re-adjudicating after seeing the split is
   what the freeze forbids. Documented in docs/METHODOLOGY.md.
5. 15 hand-checks await a human in docs/HUMAN_CHECKS.md; they sit on the ambiguous
   insulin records that decide the headline.

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
