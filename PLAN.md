# Alzheimer's repurposing workbench implementation plan

Goal: produce auditable research hypotheses from PrimeKG with graph ranking,
retrieved evidence, reproducible validation, and a cached web demo.

Architecture: pandas loads PrimeKG; a filtered Alzheimer's neighborhood becomes
a NetworkX graph. Offline jobs export rankings, paths, evidence, and evaluation
JSON. A FastAPI API and React/Cytoscape UI consume those artifacts.

## Repo layout and data flow

- `src/repurpose/data.py`: downloads, provenance, pandas loading, disease resolution.
- `src/repurpose/graph.py`: holdout removal before neighborhood extraction, graph construction.
- `src/repurpose/ranking.py`: degree-normalized mechanistic paths and popularity baseline.
- `src/repurpose/validation.py`: independent trial labels, graph-only metrics and leakage audit.
- `src/repurpose/cli.py`: reproducible offline commands.
- `src/repurpose/embeddings.py`: link prediction trained on the sanitized graph (stage 5).
- `src/repurpose/evidence.py`: retrieval, reasoning, deterministic citation checks (stage 4).
- `src/repurpose/api.py`, `web/`: cached demo API and UI (stage 3 onward).
- `tests/`: minimal leakage and citation verification tests.
- `data/raw/`: downloaded source snapshots, ignored by Git.
- `data/processed/`: sanitized graph and trial labels, ignored by Git.
- `artifacts/`: reproducible rankings, validation, and provenance for the demo.
- `README.md`, `ASSUMPTIONS.md`: commands, status, and explicit decisions.

## Build sequence

- [x] Stage 1: download PrimeKG and independently sourced Alzheimer's trial records;
  resolve IDs; remove held-out disease/drug pairs in both directions and all relation
  types before neighborhood selection, degree computation, and path scoring;
  export a 3-hop graph and explainable ranked candidates; test leakage guard; commit.
- [x] Stage 2: evaluate random, popularity, and path rankings on the same eligible
  candidate universe; export recall@10, recall@20, MRR and individual ranks;
  mark embedding/combined results unavailable until trained; commit.
- [x] First checkpoint approved by user.
- [x] Harden evaluation: separate known controls; freeze tuning/test split; add
  bootstrap intervals, secondary recall/enrichment, reverse-edge tests.
- [x] Stage 5 FIRST: timebox embedding experiments to three hours, exclude all
  held-out edges and filter negatives, tune mixture only on tuning split, compare
  once on test split. Keep path primary unless embeddings improve primary recall.
- [x] Stage-5 checkpoint approved; path-only retained after negative embedding result.
- [x] Stage 3: candidate list, interactive paths, validation dashboard using cached JSON.
- [x] Stage 4: retrieve PubMed evidence, run mechanism/safety/skeptic/synthesis roles,
  verify every cited PMID against retrieved IDs, flag unsupported claims, cache top 20.
- [x] LINCS deferred: unavailable signals have no contribution.

## Current continuation: cached-demo hardening

- [x] Verify inherited work and repair fixture regression.
- [x] Portable full-drug lookup artifact, offline mode and no-network API smoke test.
- [x] Shared live-route budget, atomic updates and fail-closed counters; regression tests.
- [x] Short README, preserved methodology, demo script and Q&A.
- [x] Final browser checks, code review and clean-checkout test (132 tests, frontend install/build); commit verified work.
- Public deployment and additional disease pilots are outside this continuation.

Each stage updates reproduction instructions and is committed separately. No scores
are probabilities of efficacy. Unknown biological direction stays unknown. Evaluation
excludes LLM outputs. Cached and live outputs must expose provenance and missing data.
