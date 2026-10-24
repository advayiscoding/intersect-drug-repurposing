# Alzheimer's drug-repurposing workbench

## Current protocol (supersedes stage-2 pool below)

The first checkpoint is approved. Evaluation hardening precedes stage 5; stop again
after stage 5. The historical stage-2 numbers below are not the new test benchmark.

**Stage 5 is complete and path-only remains primary.** The fixed DistMult experiment
did not improve primary recall. The primary report is now untuned path scoring on all
44 non-control labels with exact intervals and a family-aware permutation test; see
"Primary evaluation" below. Evidence agents are the remaining stage.

`artifacts/protocol.json` freezes the current evaluation before embedding fitting.
The original 1,801 candidates are all PrimeKG drug nodes with at least one
non-Alzheimer indication. Remove nine known Alzheimer controls, leaving 1,792.
Controls combine source PrimeKG Alzheimer indications and the sourced names in
`config/known_controls.json`. An indication does not assert current regulatory
approval. Controls are reported separately, never counted as discovery misses.

Four of the original 48 trial-tested drugs are controls: donepezil, galantamine,
rivastigmine, brexpiprazole. The other 44 are split by a fixed hash into 22 tuning
and 22 test labels. Each ranking pool excludes the opposite split's 22 positives,
leaving 1,770 candidates. This avoids treating known opposite-split labels as
negatives or letting them consume retrieval positions. All methods share this
pool and split. All target-drug edges remain absent from graph training.

Primary metrics are recall@10/20 with percentile 95% bootstrap intervals over
held-out drugs (10,000 resamples). Secondary metrics include recall@50/100,
enrichment@k = recall@k / (k / pool size), single-query MRR, and the mean reciprocal
rank across every held-out test drug. Bootstrap intervals condition on one fixed
model and graph, and do not capture model instability or biological uncertainty.
With zero observed hits they can degenerate to [0,0]; that does not establish
zero population recall. Report lift over random and popularity, not efficacy.

Mixture weights use tuning labels only; test labels are reserved until weights
and model configuration are locked. Stage-2 aggregate results were previously
seen, so this remains an internal retrospective evaluation, not a new external
validation cohort. See `context.md` for current implementation progress.

Research hypotheses, not medical advice. Stages 1–2 implement real PrimeKG loading,
Alzheimer's neighborhood extraction, explainable path ranking, leakage protection,
and a retrospective validation harness.
Embeddings and hardened evaluation are complete; UI and evidence agents remain.

## Setup and source snapshots

Python 3.11+ (developed with Python 3.12). From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test,embedding]'
repurpose validate
python -m pytest -q
```

Without installation, use `PYTHONPATH=src python3 -m repurpose.cli prepare`.
The PrimeKG CSV is approximately 937 MiB; download once. `prepare` uses pandas
chunks and builds NetworkX only from the selected subgraph. Raw sources and the
sanitized training table are local, Git-ignored files. Keep the raw snapshots for
identical reruns: ClinicalTrials.gov changes over time. SHA-256 hashes are in
`artifacts/manifest.json`.

For a **new source snapshot/experiment**, use an isolated directory. Do not replace
the frozen study's data or regenerate its split. These commands build an independent
experiment; results from changed source data are not identical reproductions:

```sh
experiment_dir=$(mktemp -d /tmp/alzheimer-experiment.XXXXXX)
mkdir -p "$experiment_dir/data/raw" "$experiment_dir/config"
cp config/known_controls.json "$experiment_dir/config/"
curl -fL --retry 3 'https://dataverse.harvard.edu/api/access/datafile/6180620' -o "$experiment_dir/data/raw/primekg.csv"
repurpose fetch-trials --root "$experiment_dir"
repurpose prepare --root "$experiment_dir"
repurpose freeze-protocol --root "$experiment_dir"
repurpose train-embeddings --root "$experiment_dir"
repurpose tune --root "$experiment_dir"
repurpose validate --root "$experiment_dir"
```

## Ranking and eligibility

The candidate universe contains all PrimeKG drug nodes with an `indication` to a
non-Alzheimer disease. That is a graph eligibility rule, **not verified regulatory
approval**. This is the original pool; known Alzheimer controls are then excluded
by the frozen registry described above. Current approval is not exhaustively audited.
Never label all entries novel repurposing discoveries or approved medications.

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
ties reproducibly, avoiding low-ID ordering. Embedding scores are now cached but
have zero primary weight after tuning; LINCS remains unavailable.

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

- `artifacts/discovery_rankings.json`: current discovery rankings, controls excluded.
- `artifacts/discovery_paths.json`: current top-20 graph explanations.
- `artifacts/known_controls.json`: separate controls and original-pool ranks.
- `artifacts/rankings.json`, `candidate_paths.json`: frozen stage-1 inputs, not UI discovery data.
- `artifacts/trial_labels.json`: matched trial IDs, names, and matching exclusions.
- `artifacts/manifest.json`: data hashes, graph counts, and leakage audit.
- `artifacts/validation.json`: split metrics, held-out drug ranks, baselines, and audit.
- `artifacts/primary_validation.json`: primary all-44 path metrics, exact intervals, family counts, permutation test.
- `artifacts/split_validation.json`: the preserved 22/22 experiment with exact display intervals.
- `artifacts/family_rankings.json`: collapsed family cards for the UI candidate list.
- `artifacts/explorer_details.json`: cached per-drug paths, graph and trial records for the UI.

These JSON files can be read without the raw dataset or network access.

## Local demo

The workbench is a React/Cytoscape frontend over a read-only FastAPI server that
returns the cached artifacts above. Nothing is computed at request time and no
network call is made while it runs.

```sh
python -m pip install -e '.[demo]'
PYTHONPATH=src python3 -m repurpose.cli prepare-ui
cd web && npm install && npm run build && cd ..
PYTHONPATH=src python3 -m uvicorn repurpose.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. `prepare-ui` rebuilds the graph from the sanitized
training edges, re-asserts that no target–drug edge survives, recomputes every path
score and refuses to write if a score disagrees with the frozen ranking. Use
`cd web && npm run dev` for the Vite dev server, which proxies `/api` to port 8000.

The **Explore** page lists the 1,781 collapsed candidate families, renders the scored
drug → protein → (protein) → disease paths in Cytoscape with optional pathway context
branches, and shows per-drug source identifiers, per-entity external links and
matched ClinicalTrials.gov records. Dashed pathway edges are sourced context and
contribute nothing to the score. Every edge is labelled direction unknown.

The graph uses a dagre layered layout running left to right. Undirected edges are
oriented by tier (drug → protein → pathway/disease) purely so the layout ranks
cleanly; this asserts no biological direction. Edge text is hidden by default —
line style plus the legend carry the relation, and the full text appears on hover or
selection. Node captions truncate at 28 characters, show the full name on hover, and
draw above every edge with a background halo. Hovering or tapping a node highlights
its connections and dims the rest. The default view shows the top 3 scored paths with
pathway context off; a toggle shows all paths, and selecting a single path turns
context back on.

`scripts/label_overlap_audit.js` measures caption collisions in the live page. Run
over the top 20 families in both the default and all-paths views (41 views): **0
label/label and 0 label/node overlaps**. Edge-through-label geometry remains in 19 of
41 views, which the draw order and halo keep legible; `artifacts/screenshots/` holds
before/after images including the worst remaining case. The **Validation** page is the
dashboard described above, including the family permutation test and the
"what didn't work" embedding note. Literature evidence is stage 4 and the panel
says so rather than showing anything unverified.

Sources: [PrimeKG repository](https://github.com/mims-harvard/PrimeKG),
[PrimeKG dataset](https://doi.org/10.7910/DVN/IXA7BM),
[ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api).

## Historical stage-2 checkpoint results (superseded)

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

At that checkpoint, embeddings were pending and four tests passed. Current stage-5
results follow. Citation checker tests still belong to stage 4, when evidence is added.

## Stage-5 checkpoint results

Test labels: 22 trial-tested drugs in 1,770 candidates, after known-control and
opposite-split exclusions. The other 22 labels were used only for mixture tuning.
Bootstrap intervals below use 10,000 resamples of test drugs. No efficacy claims.

| Method | Recall@10 [95% CI] | Recall@20 [95% CI] | Recall@50 | Recall@100 | Single-query MRR | Mean reciprocal rank, all test drugs |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Random (1,000 permutations) | 0.55% [0.47, 0.64] | 1.05% [0.95, 1.17] | 2.70% | 5.65% | 0.05498 | 0.00450 |
| Popularity | 0% [0, 0] | 0% [0, 0] | 9.09% | 9.09% | 0.02439 | 0.00488 |
| Path | 9.09% [0, 22.73] | 9.09% [0, 22.73] | 9.09% | 13.64% | 0.20000 | 0.01748 |
| DistMult embedding | 0% [0, 0] | 0% [0, 0] | 0% | 9.09% | 0.01639 | 0.00284 |
| Tuned combined | 9.09% [0, 22.73] | 9.09% [0, 22.73] | 9.09% | 13.64% | 0.20000 | 0.01748 |

The tuning split selected **path weight 1, embedding weight 0**, so combined equals
path. LINCS remains unavailable. Path recall@20 is 8.62× the sampled random mean,
or **8.05× exact random expectation** (enrichment@20). It is +9.09 percentage points
over popularity; a ratio to a zero baseline is undefined. Enrichment@10/50/100 for
paths is 16.09× / 3.22× / 2.41×. Full secondary metrics, intervals, lift and per-drug
ranks for every method are in `artifacts/validation.json`.

The two top-20 test labels are insulin detemir and insulin glulisine. Related
compounds are not independent biological discoveries; the small sample and shared
mechanism make the wide bootstrap interval especially relevant. Zero-hit intervals
for popularity and embeddings are degenerate empirical bootstraps, not proof of
zero population recall. The random CI bootstraps per-drug recovery probabilities
averaged across fixed permutations; separate random-permutation intervals are
also supplied. These are conditional intervals, not uncertainty over all models.

### Embedding experiment and leakage controls

DistMult trained from scratch on 503,473 sanitized triples: 64 dimensions, 40 fixed
epochs, at most 30,000 examples per relation per epoch, 4 type-constrained negatives
per positive, SparseAdam learning rate 0.003. This gave 6,173,400 positive example
presentations. Negative filtering rejected known triples/reverses, self-pairs,
and **all** Alzheimer/drug pairs in both directions for every relation. Tests
exercise independent forward/reverse removal and the negative filter.

The completed run took about 70 seconds on CPU. An initial run was interrupted
after epoch 1 to replace repeated membership sorting with equivalent binary
search; first-epoch loss was identical. Configuration and seed were unchanged;
no test metrics were available during this optimization. Training and experiment
preparation stayed well within the three-hour budget. This negative finding applies
to this fixed DistMult experiment, not to all embedding methods.

Mixture weights were tried at 0, .25, .5, .75, 1 using tuning recall@20 then @10,
with ties favoring path. The model and mixture were locked before test evaluation.
No new experiments were fitted after examining test performance. Source hashes,
config, training losses, selections and audits are stored in the embedding artifacts.

## Primary evaluation: all 44 discovery labels

The path hyperparameters (0.5 length penalty, −0.5 degree exponent, top-10 path sum)
were fixed before the first validation run and no weight is fitted to trial labels.
With the embedding mixture resolved to path weight 1 / embedding weight 0, no fitted
parameter remains, so the primary report evaluates **untuned path scoring on all 44
non-control trial labels** in the 1,792-drug discovery pool. The earlier 22/22 split
is preserved separately in `artifacts/split_validation.json` as the documented
model-selection experiment. Reporting all 44 after method selection is retrospective
and descriptive; it is not a fresh prospective holdout.

Displayed intervals are **95% Clopper–Pearson exact binomial** over integer drug
recoveries out of 44. Exact arithmetic does not repair dependence between
near-duplicate compounds, which the family analysis below addresses instead.

| Ranking method | Recall@10 [95% exact CI] | Recall@20 [95% exact CI] | Recall@50 | Recall@100 | Enrichment@20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Path (primary) | 9.09% (4/44) [2.53, 21.67] | 9.09% (4/44) [2.53, 21.67] | 9.09% [2.53, 21.67] | 13.64% [5.17, 27.35] | 8.15× |
| Popularity | 0% (0/44) [0, 8.04] | 0% (0/44) [0, 8.04] | 6.82% [1.43, 18.66] | 11.36% [3.79, 24.56] | 0× |
| Random (analytical k/N) | 0.56% | 1.12% | 2.79% | 5.58% | 1× |

Path recall@20 is **8.15× the exact random expectation** and **+9.09 percentage
points over popularity**; a ratio against a zero popularity baseline is undefined.
Single-query MRR is 0.2; the mean reciprocal rank across all 44 labels is 0.01536.
Random recall k/N is an analytical reference, not an estimated proportion, so no
binomial interval is attached to it.

### Drug families and biological diversity

`config/drug_families.json` explicitly groups near-duplicate compounds (insulin
variants, mecasermin formulations, citalopram/escitalopram, interferon-beta and
growth-hormone variants). This collapses the 1,792 drugs into **1,781 families** and
the 44 labels into **41 positive families**. The grouping is conservative, post-hoc,
and not an exhaustive chemical-similarity classification.

**State plainly: the recovery is essentially insulin.** Path scoring recovers 4 of 44
labelled drugs in the top 10, but those 4 span only **2 distinct families** — insulin
variants and choline — and this stays at 2 of 41 families through k=50. In the earlier
22-drug split the two top-20 hits were insulin detemir and insulin glulisine, i.e. one
drug family. Treating the hits as independent biological discoveries is not supported.

| Cutoff | Path: distinct labelled families in top-k drugs | Popularity | Random expectation |
| --- | ---: | ---: | ---: |
| Top 10 drugs | 2 | 0 | 0.25 |
| Top 20 drugs | 2 | 0 | 0.49 |
| Top 50 drugs | 2 | 3 | 1.22 |

A **family-aware permutation test** shuffles the 1,781 collapsed family cards
uniformly (10,000 permutations, each family contributing at most one positive) and
counts labelled families among the first k cards. Observed 2 families at every
cutoff: **p = 0.023 at k=10, p = 0.080 at k=20 (primary), p = 0.322 at k=50**. These
are exploratory and unadjusted, the grouping was defined after earlier results, and
none of it is an efficacy test.

Full per-method metrics, intervals, lift, family counts and provenance hashes are in
`artifacts/primary_validation.json`; the preserved split experiment with exact
display intervals is in `artifacts/split_validation.json`.

```sh
PYTHONPATH=src python3 -m repurpose.cli validate-primary
```

### Reproduce from frozen inputs

Install the embedding extra to train: `python -m pip install -e '.[test,embedding]'`.
To audit/rebuild the report from existing cached scores:

```sh
PYTHONPATH=src python3 -m repurpose.cli validate
python3 -m pytest -q
```

Training/weight-selection commands refuse to overwrite an existing fitted
experiment, preventing accidental retuning on exposed test data. To reproduce the
same experiment in a separate output directory, copy only the frozen inputs:

```sh
replay_dir=$(mktemp -d /tmp/alzheimer-replay.XXXXXX)
mkdir -p "$replay_dir/data/processed" "$replay_dir/artifacts"
cp data/processed/nodes.json data/processed/training_edges.parquet "$replay_dir/data/processed/"
cp artifacts/protocol.json artifacts/manifest.json artifacts/rankings.json artifacts/trial_labels.json "$replay_dir/artifacts/"
PYTHONPATH=src python3 -m repurpose.cli train-embeddings --root "$replay_dir"
PYTHONPATH=src python3 -m repurpose.cli tune --root "$replay_dir"
PYTHONPATH=src python3 -m repurpose.cli validate --root "$replay_dir"
```

Use identical source snapshots, Python/dependency versions and seed for comparable
reproduction. `freeze-protocol` is a one-time initial protocol-construction command,
not part of rerunning the frozen benchmark. Do not regenerate splits after results.

The future UI must read `discovery_rankings.json`, `discovery_paths.json`,
`known_controls.json`, and `validation.json`. Original `rankings.json` is the frozen
stage-1 input and includes controls; it must not be displayed as the discovery pool.
Dashboard wording must emphasize lift over random/popularity, show intervals, and
retain “trial participation does not establish efficacy.”
