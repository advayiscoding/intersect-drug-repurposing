# Disease-parameterized Parkinson's pilot — Stage 1

Goal: run the fixed path-only method on Parkinson's, then stop for review.
Setup started 2026-10-24 23:59 UTC; implementation resumed after the user's later
“continue”, with first files at 2026-10-25 04:49 UTC. Exclude the intervening idle
gap from active work. Hard timebox: three active hours; stop early if the refactor
requires unrelated product changes. One stage commit; no agent/API spending.

## Design and scope

Use a small disease-config adapter and shared pure evaluation functions, not a
second scoring implementation or a rewrite of the web app. Configs explicitly pin
PrimeKG target IDs/names, radius=3, clinical-trial condition matching, control names
and source URLs. The existing scorer and family registry remain unchanged.

Each run re-reads the source CSV with pandas. Remove all drug edges to the union
of the run's configured guarded disease targets (both orientations/all relations),
then select only that run's neighborhood. This is stronger than removing just its
trial positives and prevents another configured disease's held-out pair from
reappearing. Existing negative sampling accepts that same union of target IDs.
Single-disease Alzheimer replay uses only its original targets for parity; never
overwrite the frozen demo artifacts. Multi-disease runs default to both guards.

Outputs: artifacts/diseases/<slug>/ with manifest, rankings, path explanations,
control registry, trial labels, family cards and exact-interval validation report.
Raw trial snapshots and sanitized graph tables stay in ignored data directories.
No disease selector, new evidence, verdict changes, pooled results or plain-language
UI until the requested later checkpoints. A static checkpoint report/screenshot is
an evaluation deliverable, not a new product page.

## Tasks and file boundaries

- [x] Add config/adapter in `config/diseases.json`, `src/repurpose/diseases.py`.
  Tests: exact target resolution, invalid target/radius, source/condition isolation.
- [x] Add optional condition/output parameters in `data.py`; keep legacy defaults.
  Tests: identical trial rules, actual enrollment, experimental-arm restriction,
  Parkinson versus Alzheimer conditions and snapshot pagination.
- [x] Add `disease_pipeline.py` and CLI `fetch-disease-trials` / `run-disease`.
  Reuse graph.py/ranking.py; test immutable source, independent graph copies,
  union leakage guard before degrees and exclusion of controls from labels/pool.
- [x] Extract shared rank/family metrics from `primary_validation.py`; replay the
  original all-44 report numerically. Handle zero labels without fabricated metrics.
- [x] Download Parkinson trial snapshot, run fixed pipeline once, inspect labels
  and exclusions, capture counts/recall/CIs/MRR/lift/family permutation output.
- [x] Full test suite; confirm demo-safe and original artifacts unchanged; save
  checkpoint screenshot, update README/ASSUMPTIONS/context, one commit, STOP.

Commands: `python3 -m pytest -q`; `PYTHONPATH=src python3 -m repurpose.cli
fetch-disease-trials --disease parkinsons`; `PYTHONPATH=src python3 -m repurpose.cli
run-disease --disease parkinsons`.

Safety text on new reports: “Research hypothesis, not medical advice. This tool
does not tell anyone what to take. Talk to a doctor or pharmacist about any
medicine.” Trial participation is not evidence of benefit. No model or parameter
selection is permitted after viewing Parkinson's results.
