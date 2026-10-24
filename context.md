# Handoff context

Updated: 2026-10-24. Workspace: /Users/advay/Downloads/Hackathon.

## Session update 2026-10-24 (agent: Claude)

Independent Step-0 verification of the previous handoff: 20 tests pass (not 18;
family/exact-CI tests were added). `validate` and `validate-primary` both reproduce
their cached artifacts exactly. Leakage guards read and confirmed: target-drug
removal is symmetric, relation-agnostic, applied to ALL drugs before neighborhood
selection and degree computation; the negative sampler rejects every target/drug
pair in both orientations for every relation, so held-out positives can never be
sampled as negatives. No discrepancy in any reported number.

Committed since then:
- 72f1809 evaluation fixes (all-44 untuned path primary, Clopper-Pearson exact
  intervals, explicit drug families, family-aware permutation test).
- Stage 3 UI commit below.

Fixed a real bug found during stage 3: `build_graph` stored the edge provenance
under the key `source`, which `ranking.py` then spread over the path edge's
`source` endpoint, so every cached path edge had `"source": "PrimeKG"` instead of a
node id. The attribute is now `provenance`. Path scores are unaffected;
`artifacts/discovery_paths.json` and `candidate_paths.json` still carry the old
broken shape and are frozen stage-1/2 inputs, so the UI reads
`explorer_details.json` instead.

Stage 3 is DONE and verified in a real browser against the real caches.

Stage 3 approved. Working through Part A (node links), Part B (graph readability),
Part C (stage 4 evidence agents), one commit each.

Part A DONE. `src/repurpose/links.py` builds a per-entity external page from the
node's own source/source_id; `prepare-ui` stamps `url` onto every cached node and
the UI shows "Open in {source}" or an explicit no-link note, with the Dataverse DOI
kept as a small secondary line. All external anchors use rel="noopener noreferrer".
Node types in the UI: REACTOME pathway, NCBI gene, DrugBank drug, MONDO disease
(linked), MONDO_grouped disease (no link). The stat-card caption now derives from
`recovered_families_at_k` in primary_validation.json instead of hardcoded text.
Spot-checked live: Reactome, Monarch MONDO, DrugBank and the NCT trial page all
resolve to the right entity. NCBI Gene and AmiGO serve bot checks to automation.

Part B DONE. Graph panel rebuilt for readability: dagre layered layout (rankDir LR,
edges oriented by tier so ranks run drug -> protein -> pathway/disease), no edge
text by default (line style + legend carry the relation; full text on hover or
selection), node captions truncated at 28 chars with the full name on hover,
labels drawn above edges with a halo, hover/tap highlights connected edges and dims
the rest, and the default view shows the top 3 paths with pathway context off and a
"show all paths" toggle. `scripts/label_overlap_audit.js` measures label collisions;
run over the top 20 families in both views (41 views): 0 label/label and 0
label/node overlaps. Edge-through-label geometry remains in 19 of 41 views (1-4 per
view) and is accepted because the halo and draw order keep captions legible; the
worst case is saved as a screenshot. Before/after screenshots in
artifacts/screenshots/.

Part C (stage 4) DONE. Five roles: deterministic PubMed retriever
(`pubmed.py`, disk cache under data/cache/pubmed, E-utilities throttle, NCBI key
from .env) plus mechanism analyst, safety analyst, skeptic and synthesiser in
`agents.py` on claude-sonnet-5. `citations.py` is the deterministic span checker:
PMID must be in that family's retrieved set and the 8-40 word quote must appear
verbatim in that record's title or abstract after unicode/whitespace normalisation;
failures are flagged "unverified" in the UI and never shown as supported.
`evidence.py` caches per family (never per variant) to artifacts/evidence.json;
`build-evidence --limit 20` builds it, `--family` and `--refresh` scope reruns.
API: /api/evidence/{family_id}, with ?live=1 re-running the agents and falling back
to cache on error, labelling each result cached or live. Agent output never feeds
the ranking or validation. Keys live in a Git-ignored .env (user-supplied; be
sparing, limited credits). Notable finding: the #1 ranked family, mecamylamine, is a
nicotinic ANTAGONIST that blocked nicotine's cognitive enhancement in the retrieved
animal work, with no human Alzheimer evidence - a good honest demo beat.

Cache results for the top 20 families: 229/231 claims verified (0.87% failure),
17 of 20 families produced at least one verified claim. The 3 without any
(Dipivefrin, Zofenopril, Itopride) retrieved ZERO PubMed records for their query,
and the agents correctly reported that nothing was retrieved rather than inventing
support. Both failures were length-window rejections (one 42-word quote, one 4-word
quote), not fabricated citations or PMIDs. Rebuilding costs real credits: use
--family to scope reruns and do not pass --refresh casually.

## Feature 1: evidence gap map (DONE)

Verified no secret ever reached git history before starting: `.env` was never added
in any commit, neither key value appears in any commit, and there is no `sk-ant-`
literal anywhere in history.

`gapmap.py` derives, per reviewed family, a verdict from VERIFIED claims only plus a
direction signal, then a triage group. Exact vocabularies are in the README and in
the module. Two traps found and handled while building it: "inhibit" is NOT an
opposing word (an MAO inhibitor inhibits by design), and a harm noun alone is not
harm ("reducing behavioural deficits" is protective, so a harm verb AND noun are
required with no protective word present). Both are regression-tested.

Top 20 split: 12 supported but untested, 2 already in trials, 3 contested or
possible wrong direction, 3 insufficient evidence retrieved. Artifact
artifacts/gap_map.json via `build-gap-map`; served at /api/gap-map; third nav page
in the UI with cards that cross-link into the Explore graph and evidence tabs.
Display-only: it never re-enters ranking, validation, or agent prompts.

## Status and mandatory next action

Stage 5 approved. ACTIVE: quick all-44/family/exact-CI evaluation fixes, then stage3
local UI with real caches. STOP and report after UI works; agents stage4 follow
after that checkpoint. No further embedding work. Latest request supersedes
older status sections below. Include remaining-time estimates in reports.

User's remaining order after next approval: stage 3 UI on real cached outputs,
then stage 4 evidence agents with citation checks; optional LINCS last.
Update context.md after every meaningful change, assumptions in ASSUMPTIONS.md,
commands/results in README.md, commit each stage. Work autonomously within scope.

## Completed commits

- 874cde3: stage 1, real PrimeKG and leakage-safe path ranking.
- 9b19251: stage 2, original retrospective evaluation.
- 8544c49: evaluation hardening, controls and frozen split.
- Stage-5 code/results/docs are committed with this handoff under
  "feat: evaluate sanitized embeddings and retain path ranking after negative finding".
  Use git log for its hash.

## Sources and local environment

- System Python 3.12 has pandas 2.3.3, NetworkX 3.6.1, torch 2.12.0, NumPy, pyarrow,
  requests and pytest. Torch CPU, two threads. No venv created.
- Git/network require escalation; previous Git and curl approvals succeeded.
- PrimeKG data/raw/primekg.csv: 981,751,236 bytes, Dataverse file 6180620.
  MD5 matches published metadata: aac8191d4fbc5bf09cdf8c3c78b4e75f.
- data/raw/trials.json: 2,615 completed/terminated CT.gov records, 123 MiB.
- Source graph: 129,375 nodes, 8,100,498 reciprocal rows.
- Five Alzheimer disease nodes, excluding explicitly non-Alzheimer entity.
- Remove ALL 146 target/drug rows in both orientations/all relations before selection.
- Selected 3-hop typed graph: 29,216 nodes, 503,232 pairs, 503,473 typed triples.
- ONLY data/processed/training_edges.parquet may be used for training.
  The exploratory data/processed/edges.parquet is UNSANITIZED; never train on it.
- Raw/processed files are Git-ignored. Model data/processed/distmult.pt is local.
  All source/training hashes are in artifacts. No API credentials requested yet.

## Protocol and eligibility

- Original pool: 1,801 PrimeKG drugs with a non-Alzheimer indication.
- Known controls: union of PrimeKG Alzheimer indications and sourced treatment
  names in config/known_controls.json (NIA/FDA sources). Graph indication is not
  a claim of current regulatory approval. Combination approval is not assigned
  to individual ingredient nodes.
- Nine controls removed from discovery, leaving 1,792.
- Original 48 matched trial labels: four controls (donepezil, galantamine,
  rivastigmine, brexpiprazole) removed from discovery numerator AND denominator.
- Remaining 44 labels split by fixed hash into 22 tuning and 22 test labels.
- Each evaluation pool excludes opposite-split positives, N=1770 for each.
- artifacts/protocol.json frozen BEFORE training; do not regenerate after results.
- Trial inclusion: explicit Alzheimer condition, interventional treatment,
  completed/terminated, actual enrollment >0, DRUG in experimental arm.
- Exact normalized name/alias matching; 576 eligible trials, 79 matched drugs;
  31 lacked non-Alzheimer indications. No fuzzy matching.
- Historical aggregate stage-2 results were already seen; new split is an internal
  retrospective evaluation untouched by subsequent fitting, not new external data.
- Ground truth is independently trial-tested drugs, NOT efficacy. Symptom studies
  are included. Direction unknown on all PrimeKG paths.

## Embedding experiment (finished; no more fitting after test exposure)

- DistMult from scratch, dimension 64, 40 fixed epochs, max30k triples/relation/epoch,
  batch2048, 4 type-constrained negatives/positive, SparseAdam lr .003, seed20261024.
- 503,473 source triples; 6,173,400 positive presentations.
- Negatives reject known triples/reverses, self-pairs, and ALL Alzheimer/drug pairs
  in either orientation and every relation; protects all held-out positives.
- Completed run ~70 seconds. Initial attempt stopped after epoch1 (~101 seconds)
  to replace slow repeated np.isin sorting with equivalent searchsorted lookup.
  First-epoch loss identical; same config/seed, no test scores seen at that time.
- Config, training history, hashes, scores in embedding_config/run/scores.json.
- Mixture percentile weights tried {0,.25,.5,.75,1} only on tuning recall@20 then @10.
  Ties favor path. Selected path=1, embedding=0, LINCS=unavailable.
- Fixed DistMult did NOT improve primary recall; path remains primary.
- Finding is specific to this experiment; no claim all embeddings fail.

## Current test results

22 test positives / 1770 candidates. Recall values below are percentages.
MRR_q = reciprocal first relevant rank for one Alzheimer query.
MRR_all = average reciprocal rank across ALL 22 test drugs, not only top-k hits.

| Method | R10 | R20 | R50 | R100 | MRR_q | MRR_all |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random 1000 runs | .554545 | 1.054545 | 2.704545 | 5.645455 | .05497550 | .004495295 |
| Popularity | 0 | 0 | 9.090909 | 9.090909 | .02439024 | .004883710 |
| Path | 9.090909 | 9.090909 | 9.090909 | 13.636364 | .2 | .017484527 |
| Embedding | 0 | 0 | 0 | 9.090909 | .01639344 | .002841816 |
| Combined (path weight1) | 9.090909 | 9.090909 | 9.090909 | 13.636364 | .2 | .017484527 |

- Path/combined primary recall CIs [0,22.7273%]; random R10 [.4727,.6364%],
  R20 [.9455,1.1682%]; zero-hit empirical CIs [0,0] are degenerate, not proof.
- Bootstrap 10k resamples of test drugs, conditional on fixed graph/model/pool.
- Path EF20=8.04545 versus exact random k/N; sampled random lift=8.62069x.
  +9.0909 percentage points vs popularity; zero-baseline ratio undefined.
- Top-20 test hits: insulin detemir and insulin glulisine; correlated compounds
  limit diversity and invalidate treating hits as independent biological discoveries.
- Full CIs, enrichment@10/20/50/100, lift, controls and per-drug ranks in validation.json.
- Primary metrics R10/R20; secondary R50/R100 and enrichment.
- 18 tests pass: reverse leakage, negative filtering, numerical metrics, bootstrap,
  tuning isolation, and cached-report/control/split invariants. Compile/diff checks pass.

## Files and artifact contract for next agent

src/repurpose/:
- data.py: pandas source loading, hashes, CT.gov retrieval/matching.
- graph.py: target resolution, all-target/drug removal, neighborhood, NetworkX.
- ranking.py: fixed degree-normalized typed 2/3-edge paths; top10 sum, top5 explanations.
- protocol.py: one-time immutable control/split definition.
- evaluation.py: bootstrap/recall/enrichment/MRR/random baseline.
- embeddings.py: DistMult trainer, filtered negative sampler.
- selection.py: tune on tuning IDs only; immutable mixture selection.
- report.py: frozen protocol/hash and graph recomputation audit, test evaluation, UI exports.
- validation.py: dispatcher + legacy stage-2 implementation.
- cli.py: fetch-trials, prepare, freeze-protocol, train-embeddings, tune, validate.

UI (stage 3, built): `src/repurpose/api.py` serves cached artifacts read-only;
`src/repurpose/ui_data.py` (`prepare-ui`) writes `artifacts/explorer_details.json`
(16 MB, per-drug paths + Cytoscape graph + deduped trial records) after re-asserting
no leakage and re-checking every path score against the frozen ranking. Frontend is
`web/` (React 19, Vite 6, Cytoscape 3.30), built to `web/dist` which is Git-ignored.
`.claude/launch.json` starts uvicorn with `--app-dir src` on port 8000.
Verified in-browser: family list collapses variants, path selector isolates single
paths, trial records show real NCT ids, validation dashboard matches the artifacts.

UI must consume:
- artifacts/discovery_rankings.json (1792 controls-excluded candidates)
- artifacts/discovery_paths.json (top20 explainable paths)
- artifacts/known_controls.json (separate controls)
- artifacts/validation.json (v2 test metrics, CIs, caveats)
Original rankings.json/candidate_paths.json remain unchanged frozen source inputs;
they contain controls and must NOT be used for the discovery UI.
No frontend/API, evidence agents, citation checker or LINCS yet.

Dashboard language: lift over random/popularity, show CIs and the caveat "trial
participation does not establish efficacy." Do not say "finding Alzheimer's drugs".

## Reproduction

README has full original-source and isolated frozen-input replay commands.
In existing workspace:
PYTHONPATH=src python3 -m repurpose.cli validate
python3 -m pytest -q

Training and tuning refuse to overwrite a fitted experiment. Reproduce into a new
directory with copied frozen protocol/rankings/labels/manifest and sanitized
training_edges.parquet + nodes.json, then train-embeddings, tune, validate.
Do not refetch trials, mutate frozen inputs or regenerate the split to reproduce.
Model rankings and data are cached; no network is needed to audit scores.

## Next action

Implementing explicit drug_families config, families.py, primary_validation.py.
New artifacts primary_validation, split_validation (exact display CIs), family_rankings.
Primary results: 4/44 at k10/20/50 (9.09%), exact CI [2.5328,21.6687%]; two
distinct families (insulin, choline). 1781 total families, 41 positive families.
Family-card permutation p20=.079892 (10k permutations); exploratory post-hoc.
Added ui_data.py to cache real paths and actual protein/pathway context per drug;
api.py serves cached JSON and built frontend; no evidence agents yet.
Added explicit family and exact-CI tests; web React/Vite/Cytoscape dependency
manifest created. Installing dependencies next; no UI server yet.
Then build React/Cytoscape + FastAPI local UI, cache actual graphs and pathway context,
verify in browser, commit and STOP. Stage4 will cache top20 FAMILIES, 1–2 live queries.
No extra features or new benchmark/model selection after this exposed test result.
