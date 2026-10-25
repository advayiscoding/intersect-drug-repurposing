# Alzheimer's workbench: methodology and experiment history

Commands below assume the repository root. Start with [the README](../README.md)
for the current cached demo. Historical checkpoint tables are retained for audit;
the all-44 exact-interval report is primary, not the earlier bootstrap tables.

## Current protocol (supersedes stage-2 pool below)

Stages 1–5, the UI and evidence agents are complete. Historical stage-2 numbers
below are not the primary benchmark.

**Stage 5 is complete and path-only remains primary.** The fixed DistMult experiment
did not improve primary recall. The primary report is now untuned path scoring on all
44 non-control labels with exact intervals and a family-aware permutation test; see
"Primary evaluation" below. Evidence agents are display-only, excluded from evaluation.

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
Embeddings, hardened evaluation, UI and evidence agents are complete.

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
returns cached artifacts. Cached views require no external network calls; optional
live agent runs do. Set REPURPOSE_OFFLINE=1 for a strictly cached demo.

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

## Evidence agents

Five roles produce the literature review shown in the Explore page's **Literature
review** tab. They run **per family, never per variant**, and their output never
enters the ranking or the validation metrics.

1. **Retriever** (`pubmed.py`, deterministic, no model): one relevance-ranked PubMed
   query per family through NCBI E-utilities. Every response is cached to
   `data/cache/pubmed/` before use, throttled to the E-utilities limit (10 req/s with
   `NCBI_API_KEY`, 3 without), and a failure with no cached copy is reported rather
   than silently returning an empty set.
2. **Mechanism analyst** — what the records report about the drug/biology link, with
   the direction of any effect only where a record states it, otherwise
   "direction unknown".
3. **Safety analyst** — reported adverse effects and population cautions, and an
   explicit note when the records are silent, since silence is not evidence of safety.
4. **Skeptic** — null results, small samples, surrogate endpoints, population
   mismatch, missing Alzheimer-specific evidence.
5. **Synthesizer** — a neutral summary over the other three plus open questions.

The runtime model is **`claude-sonnet-5`** via the Anthropic API. The key is read from
`ANTHROPIC_API_KEY` (or a Git-ignored `.env`) and is never committed. With no key the
app still runs entirely from the cached review and the UI says live queries are
unavailable.

### Span-level citation verification

`citations.py` decides what the UI may show as supported, and it calls no model.
Every claim must carry a PMID **and** a verbatim quote of 8–40 words. The checker
normalizes case, whitespace and unicode punctuation, then requires that the PMID is in
the retrieved set *for that family* and that the quote appears in that record's title
or abstract. A claim citing a PMID the agent was never shown fails even if the PMID
exists in PubMed. Failing claims are flagged "unverified" in the UI with the reason
and are never presented as supported. `tests/test_citations.py` covers a valid quote,
a fabricated quote, a real PMID with a mismatched quote, a PMID outside the retrieved
set, and quotes below and above the length window; `tests/test_agents.py` runs the
whole orchestration against a stub client to confirm only verifiable claims survive.

```sh
PYTHONPATH=src python3 -m repurpose.cli build-evidence --limit 20
PYTHONPATH=src python3 -m repurpose.cli build-evidence --family "Insulin variants" --refresh
```

Reviews are cached for the top 20 families in `artifacts/evidence.json`. The UI labels
each review **cached** or **live**; `GET /api/evidence/{family_id}?live=1` re-runs the
agents and falls back to the cached review on timeout or error, reporting why. Families
outside the cached top 20 show "not reviewed" rather than anything ungrounded. Every
agent view carries the research-hypothesis banner and no agent text may claim efficacy.

## Evidence gap map

A display-only triage view over the top 20 reviewed families, combining three inputs
that already exist in the repository: the frozen **path strength**, an **evidence
verdict** derived from the verified agent claims, and **trial status** from the
matched ClinicalTrials.gov records. Nothing here feeds the ranking or the validation
metrics, and the dashboard keeps its statement that validation covers the graph
ranking alone. These are triage categories for researchers, **not a ranking of which
drugs work**.

```sh
PYTHONPATH=src python3 -m repurpose.cli build-gap-map
```

### Verdict rules (deterministic, verified claims only)

Unverified claims are ignored entirely. Each claim's free-text `evidence_type` tag is
first normalized onto one tier: a tag containing "animal", "in vivo", "mouse" or
"rodent" → **animal**; "vitro" or "cell" → **in vitro**; "human", "clinical",
"patient", or starting with "trial" → **human trial**; "review" or "meta" →
**review**; anything else → **other**. The reported `direction` string is classified
as **opposing** if it contains `block`, `antagoni`, `abolish`, `oppos`, `exacerbat`,
`worsen` or `detriment`, or if it contains both a harm verb (`induc`, `caus`,
`contribut`, `produc`, `lead to`, `result in`) **and** a harm noun (`impair`,
`deficit`, `toxicit`, `decline`, `dysfunction`, `damage`) with no protective word
(`amelior`, `attenuat`, `protect`, `improv`, `reduc`, `decreas`, `slow`, `rescu`,
`restor`, `prevent`); as **contested** if it contains `mixed`, `unclear`, `conflict`,
`contested`, `inconsistent`, `not uniform`, `varies`, `vary` or `contradict`;
otherwise **neutral**. `inhibit` is deliberately not an opposing word, because enzyme
inhibition is the intended mechanism of several candidates here. Requiring a harm verb
*and* noun keeps "reducing behavioural deficits" from reading as harm.

The first rule that matches wins:

| Verdict | Rule |
| --- | --- |
| **none in the retrieved set** | Zero verified claims. |
| **possible wrong direction** | Direction signal is opposing. |
| **mixed or contested** | Direction signal is contested. |
| **supported by human evidence** | At least one verified claim on the human trial tier. |
| **animal or in vitro only** | Verified claims exist, none on the human trial tier (animal, in vitro, review or other). |

**Verdicts are rule-based heuristics**, not clinical judgements: fixed keyword
vocabularies over the agent's reported direction, plus the evidence-type tags it
attached to each verified claim. They say what *kind of record* was cited, not
whether the evidence is about Alzheimer's or whether the drug works. Every card
shows the supporting quote so a reader can check the label against the source.

### Grouping rules

| Group | Rule |
| --- | --- |
| **already in trials** | At least one matched ClinicalTrials.gov record for any family member in this snapshot. A registered trial is a fact and outranks every verdict; registration documents testing, not efficacy. |
| **contested or possible wrong direction** | No trial record in the dataset, and the verdict is *mixed or contested* or *possible wrong direction*. |
| **no evidence retrieved** | No trial record in the dataset, and the verdict is *none in the retrieved set*. |
| **evidence retrieved, no trial record found** | No trial record in the dataset, and the verdict is *supported by human evidence* or *animal or in vitro only*. |

### Verdict audit (self-audited, on the families the rules were tuned on)

This is a **self-audit on the same 20 families the rules were tuned on**, not an
independent evaluation. The rules were adjusted while looking at these cases, so the
agreement rate below is an upper bound and says nothing about how the rules would
behave on families they have not seen.

Every verdict was read back against the quote that drove it. **16 of 20 agree; 4 do
not.** The disagreements are all the same shape: the rules classify *what kind of
record was cited*, which is not the same as whether the evidence is about Alzheimer's
or points the right way. The four are listed openly in the table.

| # | Family | Verdict | Quote that drove it (abridged) | Agree? |
| ---: | --- | --- | --- | --- |
| 1 | Mecamylamine | possible wrong direction | "beneficial effect of nicotine was abolished in animals pretreated with … mecamylamine" | yes |
| 2 | Mecasermin | supported by human evidence | "Individuals with T21 display chronic IGF1 deficiency…" | **no** — human evidence is for IGF-1/GH-insensitivity, not Alzheimer's |
| 3 | Insulin variants | mixed or contested | "Intranasal insulin is a potential treatment … shown to increase cerebral glucose uptake" | yes |
| 4 | Cerliponase alfa | supported by human evidence | "cerliponase alfa is an enzyme-replacement therapy … developed to treat neuronal ceroid lipofuscinosis" | **no** — human evidence is for CLN2; the Alzheimer's claim is in vitro only |
| 5 | Choline | mixed or contested | "Dietary choline intake has been associated with a lower risk of cognitive dysfunction" | yes |
| 6 | Artenimol | animal or in vitro only | "Dihydroartemisinin … Improves Cognitive Function in a Mouse Model of Tauopathy" | yes |
| 7 | Iproniazid | animal or in vitro only | "iproniazid was a weak MAO inhibitor (MAOI)…" | yes |
| 8 | Dipivefrin | none in the retrieved set | — | yes |
| 9 | Zofenopril | none in the retrieved set | — | yes |
| 10 | Aluminum acetate | animal or in vitro only | "Aluminium chelator (transferrin) reverses biochemical deficiency in Alzheimer brain preparations" | yes |
| 11 | Moclobemide | supported by human evidence | "Recent randomized controlled trials have demonstrated the efficacy of … moclobemide to treat depression in Alzheimer's disease" | yes (after the fix below) |
| 12 | Pegaptanib | supported by human evidence | "VEGF inhibitors may be linked to Parkinson-like events and dementia" | **no** — that is a harm signal; it should read as a possible wrong direction |
| 13 | Teprotumumab | animal or in vitro only | "recurrent falls in an elderly woman with hyperthyroidism…" | **no** — there is no animal or in vitro evidence at all; every claim is tier "other", and the records are off-topic |
| 14 | Physostigmine | supported by human evidence | "Their efficacy in the treatment of dementing illnesses is evaluated" | yes, weakly — one human-trial claim, and partly about a derivative |
| 15 | Itopride | none in the retrieved set | — | yes |
| 16 | Cisplatin | possible wrong direction | "cause mitochondrial dysfunction, and induce DNA damage, all of which impair synaptic plasticity" | yes |
| 17 | Pargyline | animal or in vitro only | "inhibitors of both cholinesterases and monoamine oxidases…" | yes |
| 18 | Sertraline | supported by human evidence | "association between antidepressants and cognitive decline in patients with dementia" | yes, with the caveat that the direction is ambiguous |
| 19 | Nicotine | mixed or contested | "positive and negative reinforcement effects…" | yes |
| 20 | Polaprezinc | supported by human evidence | "Cochrane risk of bias tool for randomized trials…" | yes |

**Rule error found and fixed:** a review that reports randomized-trial results was
being counted as *not* human evidence, so Moclobemide — supported by RCTs of
moclobemide for depression in Alzheimer's — was labelled "animal or in vitro only"
despite having no animal or in vitro evidence at all. Reviews quoting explicit
randomized-trial phrasing now count as human evidence. A bare "clinical trial"
mention does **not** promote, because it is usually about other drugs ("numerous
clinical trials for AD have failed" — Iproniazid); both directions are regression-tested.

**The four disagreements, restated plainly:** rows 2 (Mecasermin) and 4 (Cerliponase
alfa) carry human evidence for a *different disease*; row 12 (Pegaptanib) treats a
*harm* signal as support; row 13 (Teprotumumab) wears a label that does not fit its
evidence at all.

**Known gaps, deliberately not patched:**
- *Disease relevance does not change the verdict* (rows 2, 4). A human trial of the
  drug for a different disease still reads as "supported by human evidence". This is
  now surfaced separately as a **disease-relevance tag** on every card rather than
  folded into the verdict rules — see below.
- *Harm signals found by the safety agent do not reach the direction rule* (row 12).
  I implemented and tested the obvious fix — feeding verified safety and skeptic text
  into the direction classifier — and **rejected it**: it flipped five families
  (insulin, nicotine, pargyline, physostigmine, teprotumumab) to "possible wrong
  direction" because skeptic claims routinely mention impairment when describing the
  disease itself. A worse rule is not an improvement.
- *"animal or in vitro only" fits poorly when every claim is tier "review" or "other"*
  (row 13). The tier breakdown on each card shows this directly.

### Disease-relevance tag

The verdict says what *kind* of record was cited. It does not say what condition the
evidence was collected in, so that is shown separately on each card as one of:

| Tag | Rule |
| --- | --- |
| **human evidence in Alzheimer's** | At least one verified human-tier claim whose **verbatim quote** contains "alzheimer", "mild cognitive impairment" or "amnestic". |
| **human evidence in other conditions** | Verified human-tier claims exist, but no quote names an Alzheimer's context. |
| **relevance not assessed** | No verified human-tier claim to assess. |

It is matched against the **quote**, never the agent's own sentence — an agent may
write "not adults with Alzheimer's", which would otherwise count as a match. Bare
"dementia" is excluded because it spans many diseases: cerliponase alfa's records
describe "progressive dementia in children" (CLN2), which is not Alzheimer's
evidence. Mechanism words like "amyloid" are excluded for the same reason. The tag is
deliberately conservative, so it under-claims rather than over-claims, and it
**never changes a verdict** — a regression test asserts exactly that.

Current split: **3 in Alzheimer's, 7 in other conditions, 10 not assessed.** This
immediately exposes two of the four audit disagreements: Mecasermin and Cerliponase
alfa now read "human evidence in other conditions" on their cards.

### Cache-wide verification statistics

Shown on the gap map page and stored in `artifacts/gap_map.json`:

| Measure | Value |
| --- | ---: |
| Families reviewed | 20 |
| Families with at least one verified claim | **17** |
| Claims generated | 231 |
| Claims verified | **229** |
| Claims dropped or flagged | 2 |
| Failure fraction | **0.87%** |

Both failures were quote-length rejections (one 42-word quote, one 4-word quote), not
fabricated PMIDs or quotes. The three families with no verified claim retrieved zero
PubMed records, and the agents reported that rather than inventing support.

Current split of the top 20: **12 evidence retrieved / no trial record found, 2
already in trials, 3 contested or possible wrong direction, 3 no evidence retrieved.**
Group names describe the **dataset**, not the world: "no trial record found" means
this snapshot holds no matched ClinicalTrials.gov record, never that a drug is
untested. Each card shows the verified-claim breakdown by evidence type (human trial /
animal / in vitro / review / other) and the supporting quote behind its verdict, links
to that family's graph and evidence views, and carries its cached/live label. Absence
is always phrased "none in the retrieved set", never "no evidence exists".

## Check my idea

Enter a drug and get the same treatment any ranked candidate gets: its graph paths,
the evidence agents' output, and the same verdict tag. **Alzheimer's disease is the
only disease built**, and the UI says so — the graph, the ranking and the cached
reviews are all Alzheimer-specific, so another disease would need its own
neighborhood and evaluation first.

Four outcomes, each stated plainly rather than rendering an empty page:

| Outcome | What it means |
| --- | --- |
| **resolved** | Graph paths, cached or live agent review, verdict tag. |
| **not in this graph** | The name is not a drug node in this PrimeKG snapshot — absent from this graph, not non-existent. Close matches are suggested. |
| **in the graph, no path** | The drug node exists but no drug → protein → (protein) → disease path reaches an Alzheimer node in the sanitized subgraph. |
| **unsupported disease** | Anything other than Alzheimer's. |

Names resolve case-insensitively and ignore punctuation and spacing, accept the
DrugBank identifier, fall back to a **synonym map**, and then to a leading-prefix
match so "insulin glargine injection" still resolves. Unmatched input gets close
matches from the graph's own vocabulary.

### Synonym map

PrimeKG names drugs by one preferred label, so "rapamycin" used to miss even though
the graph holds it as *Sirolimus*. `data/synonyms.json` is compiled from **PubChem**
(U.S. National Library of Medicine; its data is in the public domain), cached to
`data/cache/pubchem/` so both the build and every lookup work **offline**.

```sh
PYTHONPATH=src python3 -m repurpose.cli build-synonyms
```

Synonyms are a fallback layer only, never an override: a synonym claimed by more than
one drug node offers an explicit choice rather than resolving arbitrarily; a synonym equal to some
other node's primary name is never recorded. At most 25 synonyms per drug are kept,
and registry numbers, catalogue codes and structure strings are filtered out. A
synonym match is always **shown**, never silent — the result reads
"Matched rapamycin → sirolimus (synonym)".

**Untrusted input.** User text is sanitized to a conservative character set, stripped
of control characters and capped at 100 characters, and is used *only to look up a
node*. Every downstream consumer — the agent prompts and the PubMed query — receives
the canonical node name taken from the graph, so text appended to a drug name cannot
reach an agent instruction or widen a retrieval query. This is covered by tests that
feed in prompt-injection, markup and query-breaking strings.

### Cost safety

Three layers, in order of how much you should trust them:

1. **A hard spend limit on the API key, set at the provider.** This is the only
   control that cannot be defeated by a bug, a restart or a surprise in this code.
   In the Anthropic Console, set a workspace spend limit and issue the demo a key
   scoped to that workspace. Do this before any public deployment. Everything below
   is a convenience on top of it.
2. **A process-wide daily cap** on live agent runs: default 40, set
   `REPURPOSE_DAILY_LIVE_CAP` at deploy time. It is persisted to
   `data/cache/live_runs.json`. **On a host with an ephemeral disk — a container, a
   scale-to-zero platform, most PaaS free tiers — that file disappears on restart and
   the day's count resets to zero**, so the effective ceiling is the cap multiplied by
   however many times the host restarts. Treat it as a brake, not a budget. Mount a
   persistent volume if you need it to hold, and rely on layer 1 regardless.
3. **A per-session limit** of 5 live runs per 10 minutes, held in memory. This stops
   one impatient visitor, nothing more.

Pre-computed results for ~28 commonly tried drugs (`artifacts/check_cache.json`) are
served straight from disk and labelled "cached", so the obvious demo queries spend
nothing at all. When any cap is hit the cached review is shown with the reason
stated. API keys are read **server-side only** and never appear in any response; a
test asserts that with sentinel key values.

```sh
REPURPOSE_DAILY_LIVE_CAP=10 PYTHONPATH=src python3 -m uvicorn repurpose.api:app --app-dir src
``` A live run is
labelled "live"; on timeout, error or an exhausted allowance the cached review is
shown instead, labelled "cached", with the reason stated. Every claim passes the same
span-level citation checker, and nothing unverified is ever shown as supported.

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

All figures in this table are from the preserved 22/22 split on **raw, unaudited**
labels. They are historical and are not the current primary result.

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

**This all-44 table is the raw, unaudited, secondary result.** The primary result is
the strict evaluation in "Strict trial labels" below, which supersedes it as the
headline. Raw figures remain true of the raw label set and are kept for comparison.

| Ranking method (raw labels) | Recall@10 [95% exact CI] | Recall@20 [95% exact CI] | Recall@50 | Recall@100 | Enrichment@20 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Path (raw primary) | 9.09% (4/44) [2.53, 21.67] | 9.09% (4/44) [2.53, 21.67] | 9.09% [2.53, 21.67] | 13.64% [5.17, 27.35] | 8.15× |
| Popularity | 0% (0/44) [0, 8.04] | 0% (0/44) [0, 8.04] | 6.82% [1.43, 18.66] | 11.36% [3.79, 24.56] | 0× |
| Random (analytical k/N) | 0.56% | 1.12% | 2.79% | 5.58% | 1× |

On raw labels, path recall@20 is 8.15× the exact random expectation and +9.09
percentage points over popularity; a ratio against a zero popularity baseline is
undefined. Single-query MRR is 0.2; the mean reciprocal rank across all 44 raw
labels is 0.01536. Random recall k/N is an analytical reference, not an estimated
proportion, so no binomial interval is attached to it.
## Strict trial labels — the primary result

The rule was frozen at `c041084` before any strict assignment
([`docs/STRICT_LABEL_RULE.md`](STRICT_LABEL_RULE.md)) and the handling of ambiguity
was pre-declared before any metric
([`docs/STRICT_LABEL_PROTOCOL.md`](STRICT_LABEL_PROTOCOL.md)). Rankings, candidate
universes, controls, family assignments, path constants and leakage guards are
unchanged; only the label set differs. **Very small sample. Small test, not shown to
generalize. Trial participation does not establish efficacy.**

### Adjudication and independent review

Every raw drug–trial–intervention record was adjudicated rank-blind, then re-decided
by an independent reviewer in a fresh context with only the rule, the rank-free
source bundle and the decision file — no ranks, scores or metrics.

| Disease | Records | Agreement | Cohen's κ | Disagreements |
| --- | ---: | ---: | ---: | ---: |
| Alzheimer's | 57 | 52 (91.23%) | 0.856 | 5 |
| Parkinson's | 56 | 55 (98.21%) | 0.961 | 1 |

Each disagreement became `uncertain` under the pre-declared rule: methylene blue,
sirolimus, dapagliflozin, telmisartan, salsalate (Alzheimer's) and perampanel
(Parkinson's). After resolution: Alzheimer's 27 include / 17 exclude / 13 uncertain;
Parkinson's 38 / 15 / 3.

### Results

| Alzheimer's | Labels | Hits@10/20 | Recall | Exact 95% CI | Families | Permutation p@20 |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| **Strict (primary)** | 24 | **1** | **4.17%** | 0.11–21.12% | 1 of 23 | 0.233 |
| Strict sensitivity | 32 | 3 | 9.38% | 1.98–25.02% | 1 of 29 | 0.287 |
| Raw (secondary) | 44 | 4 | 9.09% | 2.53–21.67% | 2 of 41 | 0.080 |

| Parkinson's | Labels | Hits@10/20 | Recall | Exact 95% CI | Hits@50 | Permutation p@20 |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| **Strict (primary)** | 24 | **0** | 0% | 0–14.25% | 3 | 0.238 |
| Strict sensitivity | 26 | 0 | 0% | 0–13.23% | 3 | 0.254 |
| Raw (secondary) | 39 | 0 | 0% | 0–9.03% | 4 | 0.356 |

Popularity recovers 0 at 10 and 20 in every Alzheimer's analysis.

**The Alzheimer's recovery is one insulin.** Of the four raw top-20 hits, insulin
glulisine (rank 6) survives the strict rule; insulin aspart (rank 5) and insulin
detemir (rank 9) fall to *uncertain* on ambiguous population evidence and count only
in the sensitivity analysis; choline (rank 10) is excluded outright. The
"essentially insulin" caveat we had been reporting is literally true under audit, and
the permutation test is no longer suggestive at any cutoff. **Parkinson's remains
negative**, as it was on raw labels.

### Known limitations of this audit

- **Verdict-threshold inconsistency.** The reviewer observed that the
  `no_clinical_objective` bar lands inconsistently across four records (3TC
  included, ERAP sirolimus excluded on a similar pattern; dapagliflozin included on
  weaker clinical-limb evidence than telmisartan and salsalate, which were excluded).
  Re-adjudicating for consistency after seeing the split is exactly what the
  pre-evaluation freeze forbids, so it is reported rather than fixed. Three of the
  four were demoted to `uncertain` anyway, which resolves toward the conservative
  reading.
- **One weak identity.** In `14685:NCT00066157` the labelled identity is Progesterone
  but the registered intervention is Medroxyprogesterone, normalized through the
  registry's own `otherNames`. It satisfies the letter of Gate 1.5, but these are
  distinct molecules.
- **Self-audited verdict heuristics.** The gap-map verdicts remain keyword rules
  self-audited on the 20 families they were tuned on; see the audit table above.
- **A reviewer is not ground truth.** Two careful readings agreeing is not proof that
  either is right. The 15 hand-checks in [`HUMAN_CHECKS.md`](HUMAN_CHECKS.md) exist
  because `uncertain` records sit directly on the drugs that drove the headline.

## Drug families and biological diversity

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
