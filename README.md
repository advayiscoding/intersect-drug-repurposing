# Alzheimer's drug-repurposing workbench

Research hypotheses, not medical advice. Stage 1 implements real PrimeKG loading,
Alzheimer's neighborhood extraction, explainable path ranking, and leakage protection.
The UI, evidence agents, and embeddings are scheduled after the stage-2 checkpoint.

## Setup and source snapshots

Python 3.11+ (developed with Python 3.12). From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
mkdir -p data/raw data/processed artifacts
curl -fL --retry 3 'https://dataverse.harvard.edu/api/access/datafile/6180620' -o data/raw/primekg.csv
repurpose fetch-trials
repurpose prepare
python -m pytest -q
```

Without installation, use `PYTHONPATH=src python3 -m repurpose.cli prepare`.
The PrimeKG CSV is approximately 937 MiB; download once. `prepare` uses pandas
chunks and builds NetworkX only from the selected subgraph. Raw sources and the
sanitized training table are local, Git-ignored files. Keep the raw snapshots for
identical reruns: ClinicalTrials.gov changes over time. SHA-256 hashes are in
`artifacts/manifest.json`.

## Ranking and eligibility

The candidate universe contains all PrimeKG drug nodes with an `indication` to a
non-Alzheimer disease. That is a graph eligibility rule, **not verified regulatory
approval**. Existing Alzheimer drugs can appear as rediscovery controls; current
approval filtering is not yet implemented. Never label all entries novel repurposing
discoveries or approved medications on this basis.

Resolve Alzheimer-named disease nodes, excluding the explicitly non-Alzheimer
entity. Remove **every** drug–target-disease edge, in both directions and with any
relation type, before selecting a three-hop neighborhood. Traverse drug/protein,
protein/protein, disease/protein, pathway/protein, indication, off-label, and
contraindication edges. Collapse reciprocal copies per relation. The exported
`data/processed/training_edges.parquet` is the only allowed future embedding input.

Paths scored are drug → protein → disease and drug → protein → protein → disease.
For each path, multiply `0.5^(edge_count-2)` by the inverse square root of each
intermediate node's degree and the drug's degree, all from the sanitized subgraph.
Sum the strongest 10 paths. Keep the strongest 5 explanations. These fixed choices
are not tuned to trial labels. Edge confidences are unavailable. All biological
directions are explicitly unknown; structural traversability does not establish
activation, inhibition, blood-brain-barrier penetration, or efficacy.

Drugs outside the selected neighborhood remain in the candidate universe with
zero path score and zero local degree. SHA-256 of a fixed prefix and drug ID breaks
ties reproducibly, avoiding low-ID ordering. LINCS and embedding scores remain
missing, with their weights displayed as unavailable.

## Trial labels

Snapshot the ClinicalTrials.gov `Alzheimer Disease` query, completed/terminated
records. Locally require an explicit Alzheimer condition, interventional treatment
study, actual enrollment >0, and a DRUG intervention linked to an EXPERIMENTAL arm.
Match the intervention name or reported aliases exactly to a normalized PrimeKG
drug name. Ambiguous matches and unmatched names are excluded and reported.
This conservative procedure misses formulations, salts, and unlisted synonyms;
registration also cannot prove that every participant received a particular drug.

Ground truth means **drugs independently tested in Alzheimer's trials**, not proven
efficacy. Trials may address symptoms, may fail, and may lack published results.
The evaluation is a retrospective graph holdout, not a temporal/prospective test.

## Cached artifacts

- `artifacts/rankings.json`: scores and availability for every eligible candidate.
- `artifacts/candidate_paths.json`: top-20 candidates' graph explanations.
- `artifacts/trial_labels.json`: matched trial IDs, names, and matching exclusions.
- `artifacts/manifest.json`: data hashes, graph counts, and leakage audit.

These JSON files can be read without the raw dataset or network access. Demo server
commands will be added with stage 3; there is no web demo at this checkpoint yet.

Sources: [PrimeKG repository](https://github.com/mims-harvard/PrimeKG),
[PrimeKG dataset](https://doi.org/10.7910/DVN/IXA7BM),
[ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api).
