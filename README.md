# Alzheimer's drug-repurposing workbench

Research hypotheses, not medical advice. Stages 1–2 implement real PrimeKG loading,
Alzheimer's neighborhood extraction, explainable path ranking, leakage protection,
and a retrospective validation harness.
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
repurpose validate
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
- `artifacts/validation.json`: metrics, held-out drug ranks, baselines, and audit.

These JSON files can be read without the raw dataset or network access. Demo server
commands will be added with stage 3; there is no web demo at this checkpoint yet.

Sources: [PrimeKG repository](https://github.com/mims-harvard/PrimeKG),
[PrimeKG dataset](https://doi.org/10.7910/DVN/IXA7BM),
[ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api).

## Stage-2 checkpoint results

Evaluated 48 trial-tested drugs (83 unique matched trial records) in a fixed
1,801-drug universe. All direct Alzheimer/drug edges were removed before graph
selection. Validation independently reloads the sanitized export and recomputes
degrees and path scores, rejecting cached mismatches or changed training data.

| Method | Recall@10 | Recall@20 | MRR |
| --- | ---: | ---: | ---: |
| Random, mean of 1,000 permutations | 0.54% | 1.08% | 0.1008 |
| Popularity (sanitized subgraph degree) | 0.00% | 0.00% | 0.0313 |
| Path | 8.33% (4/48) | 10.42% (5/48) | 0.2000 |
| Embedding | unavailable | unavailable | unavailable |
| Combined | unavailable | unavailable | unavailable |

MRR follows the information-retrieval definition: reciprocal of the first relevant
rank, averaged over disease queries. Here there is only one disease query, so path
MRR is 1/5. The separate mean reciprocal rank across **all held-out drugs** is
0.01732 for paths, 0.00447 for popularity, and 0.00447 for random. Both definitions
are stored explicitly to avoid confusing the single-query result with a multi-query
benchmark. Random intervals in the JSON describe variation between permutations.

This is evidence of recovering known trial participation, not evidence of efficacy
or novel discovery. Exact matching found 79 drugs; 31 lacked a non-Alzheimer
indication and were excluded under the predeclared universe rule. 451 intervention
names did not yield an unambiguous exact match. The evaluation includes symptom
studies and existing Alzheimer drugs, and indirect historical information can
remain in a retrospective graph. No temporal generalization is claimed.

Embedding and combined results will be populated after stage 5 trains on the same
sanitized graph. Citation checker tests belong to stage 4, when evidence is added.
The four current tests cover leakage invariance and numerical metric definitions.
