# Handoff context

Updated: 2026-10-24. Workspace: /Users/advay/Downloads/Hackathon.

## Status and mandatory next action

Stage 5 and evaluation hardening are COMPLETE. Stop at the SECOND checkpoint and
wait for the user's reply. The first checkpoint was approved. Do NOT implement
UI, evidence agents or further embedding experiments until continuation.

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

Report stage-5 checkpoint and WAIT. After explicit continuation, implement stage3 UI
then stage4 evidence agents with deterministic PMID verification and top20 cache.
No extra features or new benchmark/model selection after this exposed test result.
