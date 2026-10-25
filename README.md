# Intersect · Alzheimer's research workbench

Connect PrimeKG mechanisms, independently registered trials and cited PubMed
evidence. Explore 1,781 candidate families, inspect graph paths and review cached
literature agents. **Research hypotheses, not medical advice. Trial participation
does not establish efficacy.**

## Run the cached demo

Python 3.12 and Node 20+; run from the repository root. Installation/build requires
network access; the built demo does not. No keys or raw PrimeKG download required.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[demo,test]'
npm ci --prefix web
npm run build --prefix web
REPURPOSE_OFFLINE=1 python -m uvicorn repurpose.api:app --host 127.0.0.1 --port 8000
```

Open [the local workbench](http://127.0.0.1:8000). Explore, Gap map, Check my idea
and Validation use shipped artifacts, including a complete drug-name index and
synonym map. Offline mode disables both live routes even when credentials exist.
External source links still require internet when clicked.

## What the results actually say

**Strict-label protocol (frozen before strict recalculation):** retain the raw
registry and identity filters, then require affirmative evidence that participants
have the target disease and the drug is a focal studied intervention with a clinical
objective/outcome. Exclude healthy-only, probe/interaction/PK-only, background or
unseparated co-administered agents; ambiguous records do not qualify. Diagnosed-
patient symptom studies may qualify. A drug needs at least one qualifying study.
No scores or ranking settings change. See [the fixed rule](docs/STRICT_LABEL_RULE.md)
and [the handling pre-declaration](docs/STRICT_LABEL_PROTOCOL.md).

**The strict result is the primary one, and it is weak.** Small test, not shown to
generalize; **very small sample**.

| Alzheimer's, path recall@10 / @20 | Labels | Hits | Recall | Exact 95% CI | Families recovered |
| --- | ---: | ---: | ---: | --- | ---: |
| **Strict (primary, uncertain excluded)** | 24 | **1** | **4.17%** | 0.11–21.12% | 1 of 23 |
| Strict sensitivity (uncertain included) | 32 | 3 | 9.38% | 1.98–25.02% | 1 of 29 |
| Raw, unaudited (secondary) | 44 | 4 | 9.09% | 2.53–21.67% | 2 of 41 |

Family-aware permutation p@20: **0.233 strict**, 0.287 sensitivity, 0.080 raw —
all exploratory and unadjusted. Popularity recovers 0 at 10 and 20 in every analysis.

**Under the strict rule the recovery is one insulin.** Of the four raw top-20 hits,
insulin glulisine survives; insulin aspart and insulin detemir fall to *uncertain*
on ambiguous population evidence and count only in the sensitivity analysis; choline
is excluded outright. The long-standing "essentially insulin" caveat turns out to be
literally true — strip the ambiguous records and a single insulin remains, and the
permutation test stops being suggestive at all.

The earlier 22/22 test split recovered insulin detemir and insulin glulisine at 20.
DistMult recovered 0/22 at 10/20; tuning selected zero embedding weight. Path-only
remains primary, with **no label-fitted hyperparameters**. The 22/22 experiment is
preserved, not retrained. The all-44 report is retrospective, not a fresh holdout.

Eligibility is a non-Alzheimer indication in PrimeKG, not verified regulatory
approval: 1,801 drugs minus nine known controls = 1,792 discovery drugs. Controls
are excluded, never counted as misses. All target–drug edges are removed in both
directions before graph selection, degrees and training. Graph direction is unknown.

Twenty family reviews are cached. Citation checking verifies retrieved PMID
membership and an 8–40-word source quote, **not that the interpretation is correct**.
Verdicts are heuristics, not efficacy findings; agents never affect validation.
LINCS is unavailable. [Full methodology and historical results](docs/METHODOLOGY.md).

## Verify or rebuild

### Parkinson pilot (Stage 1 checkpoint)

The product demo above remains Alzheimer-only. The isolated Parkinson pilot is
complete on `feat/parkinsons-pilot`; no disease-specific tuning or new embeddings.
The original `demo-safe` commit and artifacts are unchanged.

**No primary lift:** path recall@10/@20 is 0/39 (0%; exact 95% CI 0–9.03%),
versus popularity 1/39 (2.56%) and random expectations 0.56% / 1.13%.
There are 1,774 candidate drugs / 1,763 families and 39 registry labels / 39
families. The family permutation p@20 is 0.356. These are not 39 independent
clinical experiments: original raw label rules also admit healthy-volunteer interaction
probes. Acetaminophen's top-50 label and caffeine's popularity label are examples.
No labels were removed after seeing the result.

[Checkpoint, metrics and reproducibility](docs/PARKINSONS_CHECKPOINT.md) ·
[Cached report](artifacts/diseases/parkinsons/report.html) ·
[Screenshot](artifacts/screenshots/parkinsons-stage1.png)

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

### Original Alzheimer cached jobs

```sh
python -m pytest -q
python -m repurpose.cli validate-primary
python -m repurpose.cli build-gap-map
python -m repurpose.cli build-check-cache
```

These use frozen cached inputs. `prepare-ui` additionally needs the original
ignored processed graph. [Methodology](docs/METHODOLOGY.md) covers source download,
provenance, the frozen split, embedding reproduction and paid evidence jobs.

Optional live runs need `pip install -e '.[agents]'`, server-only API credentials
and offline mode unset. Both routes enforce a shared daily cap (default 40,
`REPURPOSE_DAILY_LIVE_CAP`) and a session limit. Counter updates are locked and atomic
on macOS/Linux; daily reset is UTC. Failed attempts consume budget. Ephemeral disks
or separate replicas can reset/multiply limits: configure a provider-side spending
limit. Do not expose live endpoints publicly without access control.

[Three-minute demo and Q&A](docs/DEMO.md) · [Handoff](context.md) ·
[Assumptions](ASSUMPTIONS.md)
