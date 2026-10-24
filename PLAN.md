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
- [ ] Stage 2: evaluate random, popularity, and path rankings on the same eligible
  candidate universe; export recall@10, recall@20, MRR and individual ranks;
  mark embedding/combined results unavailable until trained; commit.
- [ ] STOP at the user checkpoint: report actual metrics, working components,
  limitations, and wait for a reply before stage 3.
- [ ] Stage 3: candidate list, interactive paths, validation dashboard using cached JSON.
- [ ] Stage 4: retrieve PubMed evidence, run mechanism/safety/skeptic/synthesis roles,
  verify every cited PMID against retrieved IDs, flag unsupported claims, cache top 20.
- [ ] Stage 5: train embeddings on the sanitized graph, score candidates, evaluate
  embedding and combined rankings with the same held-out labels; preserve split provenance.
- [ ] Stage 6: optional LINCS reversal if usable signatures exist; unavailable signals
  have no contribution and display an unavailable weight.

Each stage updates reproduction instructions and is committed separately. No scores
are probabilities of efficacy. Unknown biological direction stays unknown. Evaluation
excludes LLM outputs. Cached and live outputs must expose provenance and missing data.
