# Stage 1 checkpoint: Parkinson's pilot

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

**No lift over random or popularity at the primary cutoffs.** The fixed path
method recovered 0/39 registry labels at both 10 and 20 drugs. No parameter,
family assignment, candidate or label was changed in response to the results.
The next stage is paused for the user's decision.

## Results

Pool: 1,801 drugs with a source PrimeKG indication outside the selected Parkinson
targets, minus 27 known controls = **1,774 discovery drugs / 1,763 families**.
This eligibility rule does not assert regulatory approval. Controls are separated,
not counted as misses. The named control list is supplemented by every source
target-indication drug; excluded controls retain their provenance in JSON.

CT.gov snapshot: 2026-10-25 04:52:49 UTC, 2,922 records over 3 pages. The unchanged
matcher admits 547 trials and matches 71 graph drug identities. Eighteen matched
controls and 15 drugs outside the initial universe are excluded (one overlaps),
leaving **39 labels / 39 distinct families under the frozen registry**. Families
are conservative identity groups, not independent studies or biological mechanisms.

| Ranking | Recall@10 (primary) | Recall@20 (primary) | Recall@50 | Recall@100 |
| --- | --- | --- | --- | --- |
| Path-only | 0/39, 0% [0–9.03] | 0/39, 0% [0–9.03] | 4/39, 10.26% [2.87–24.22] | 6/39, 15.38% [5.86–30.53] |
| Popularity | 1/39, 2.56% [0.06–13.48] | 1/39, 2.56% [0.06–13.48] | 1/39, 2.56% [0.06–13.48] | 1/39, 2.56% [0.06–13.48] |
| Random expectation | 0.56% | 1.13% | 2.82% | 5.64% |

Brackets are 95% Clopper–Pearson intervals, in percent. Random recall is exactly
min(k,N)/N, not an estimated binomial proportion. At 20, path lift is **0× random**
and **−2.56 percentage points versus popularity**. Secondary enrichment factors
are 3.64× at 50 and 2.73× at 100; these do not rescue the primary result.

| Ranking | Single-query MRR | All-label mean reciprocal rank |
| --- | ---: | ---: |
| Path-only | 0.04348 | 0.006118 |
| Popularity | 0.11111 | 0.005955 |
| Random (1,000 permutations) | 0.08173 | 0.004417 |

| k | Path families within top-k drugs | Path labels in top-k family cards | Family permutation p |
| --- | ---: | ---: | ---: |
| 10 | 0 | 0 | 1.000 |
| 20 | 0 | 1 | 0.356 |
| 50 | 4 | 4 | 0.0235 |

These are different ranking units. Collapsing variants moves Sertraline at drug
rank 23 into the first 20 family cards. The null permutes 1,763 family units
10,000 times; k=20 is primary, 10/50 are descriptive and unadjusted. Within top-50
drugs the recovered families are Acetaminophen, Buspirone, Cannabidiol and
Sertraline. Popularity recovers one family (Caffeine) at each listed cutoff.

## Label audit and limits

The endpoint is **registered experimental-arm drug occurrence in Parkinson-tagged
trials under the inherited filters**, not disease-patient benefit or disease-
directed testing. Trials must be interventional, completed/terminated, primary
purpose TREATMENT, actual enrollment >0, with a DRUG in an EXPERIMENTAL arm and an
exact normalized name/alias match. Condition tags alone do not identify a cohort.

- [NCT02305017](https://clinicaltrials.gov/study/NCT02305017): healthy-volunteer
  opicapone/paracetamol pharmacokinetic study. Acetaminophen, path rank 44, matches
  the registered alias; this is one of four top-50 hits.
- [NCT03970798](https://clinicaltrials.gov/study/NCT03970798): healthy-volunteer
  interaction study of KW-6356. Caffeine, midazolam and rosuvastatin are explicitly
  described as index substrates. Caffeine is the sole popularity top-10 hit.

Both records set `healthyVolunteers=true`; their experimental-arm assignments and
primary-purpose fields pass the frozen rules. This issue was discovered in review
after evaluation. Only descriptive metadata was corrected; the sample, scores and
metrics remain frozen. A stricter cohort/intervention-role protocol would be a
separate, explicitly approved analysis, not a silent replacement of this result.

The label sample is small and incomplete. Related drugs and shared trials violate
simple independence assumptions. Family grouping does not correct registry-role
confounding. Trial participation does not establish efficacy. Source graph edges
have direction unknown. This is retrospective graph holdout, not temporal validation.
No embeddings were run: the earlier Alzheimer DistMult result was negative and
embedding development remains stopped. LINCS unavailable; agents were not evaluated.

## Refactor and verification

Three existing modules changed: trial matcher/download parameters, CLI routing,
and extraction of shared statistics. Two new modules hold config validation and
isolated runs. A standalone renderer produces this checkpoint's HTML from JSON.
Scorer, graph implementation, embedding code, family registry, product UI and
original cached artifacts are unchanged. The complete Alzheimer replay preserves
every drug's path rank, path score, degree and path count, and its aggregate metrics.
Random-family expectations differ at most by floating-point summation precision.

Each disease run freshly loads pandas data, removes all drug pairs to the union
of five Alzheimer and six Parkinson targets in both directions/all relations,
then builds only its own three-hop NetworkX neighborhood. Parkinson removed 382
source rows; its graph has 29,177 nodes and 503,064 training triples. Actual saved
training data was audited for zero guarded pairs. Negative sampling's existing
union filter is tested; no model was trained. An explicit guard override cannot
disable the union, except the named Alzheimer snapshot parity replay.

Setup began at 23:59 UTC; implementation resumed at 04:49 UTC after an idle gap.
Active implementation/review was about 15 minutes, plus initial setup—not five
hours of continuous work. Each full raw-data pipeline run took about 22 seconds.
No paid LLM calls or deployment. The original `demo-safe` tag pins d35abee.
Verification: 144 tests pass and the unchanged frontend builds. Remaining warnings
are the pre-existing Starlette/httpx deprecation and Vite main-chunk size warning.

## Reproduce or inspect

Cached verification and report rendering need no credentials or raw dataset:

```sh
python3 -m pytest -q
python3 scripts/render_disease_report.py artifacts/diseases/parkinsons
python3 -m http.server 8012 --bind 127.0.0.1 --directory artifacts/diseases/parkinsons
```

Open `http://127.0.0.1:8012/report.html`. JSON files include rankings, top-20 drug
paths, family cards, controls, trial links, statistics and frozen input hashes.
This is a checkpoint report, not the later multi-disease product UI.

To replay from local raw inputs without overwriting the frozen result:

```sh
PILOT_ROOT="$(mktemp -d /tmp/intersect-pilot.XXXXXX)"
cp -R config src "$PILOT_ROOT/"
mkdir -p "$PILOT_ROOT/data/raw/parkinsons"
ln -s "$PWD/data/raw/primekg.csv" "$PILOT_ROOT/data/raw/primekg.csv"
cp data/raw/parkinsons/trials.json "$PILOT_ROOT/data/raw/parkinsons/trials.json"
PYTHONPATH=src python3 -m repurpose.cli run-disease --root "$PILOT_ROOT" --disease parkinsons
```

Raw CSV and trial snapshots are Git-ignored; hashes are in the manifest. Without
the snapshot, `fetch-disease-trials --root "$PILOT_ROOT" --disease parkinsons`
fetches a new version (network), not an exact replay; use a fresh directory first.
Completed runs refuse overwrite. The Alzheimer parity command is `run-disease
--disease alzheimers --guard-disease alzheimers --trials-snapshot data/raw/trials.json`
in a fresh experiment root containing that snapshot. Do not delete shipped results
to rerun. Screenshots: `artifacts/screenshots/parkinsons-stage1*.png`.
