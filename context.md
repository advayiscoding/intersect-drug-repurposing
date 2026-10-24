# Handoff context

Updated: 2026-10-24. Workspace: `/Users/advay/Downloads/Hackathon`.

## Persistent instructions

- Solo 24-hour Alzheimer's hackathon. Approved scope and stage order in PLAN.md.
- Work autonomously, commit each stage, record assumptions and reproduction commands.
- **STOP after stage 2, report measured results, and wait for user reply before stage 3.**
- Update context.md after each meaningful code/artifact change.
- Trial testing is not efficacy; no invented evidence or validation results.

## Status

- Stage 1 committed: `874cde3`. Stage 2 implemented and validated; its code, results,
  and this handoff are committed together as `feat: validate graph rankings against independent Alzheimer trials`.
- Mandatory checkpoint reached. Report results and WAIT for the user's reply.
- Stages 3 UI, 4 evidence/citations, 5 embeddings, 6 optional LINCS are unimplemented.
- No credentials needed/requested yet. System Python 3.12 has required packages.
- Git writes and network access require escalation; Git/curl approvals succeeded.

## Files and data

- data.py: pandas loading, hashes, CT.gov download and exact name/alias matching.
- graph.py: remove all drug/Alzheimer pairs, both directions/all relations, before
  three-hop extraction, degree normalization, and NetworkX construction.
- ranking.py: deterministic typed paths, top-10 sum, top-5 explanations, hashed ties.
- cli.py: fetch-trials, prepare, validate. Source files are under src/repurpose/.
- tests/test_leakage.py: 2 tests passed at stage 1; injected labels cannot alter
  training triples, graph membership, degrees, or path rankings.
- artifacts/: committed rankings, top-20 candidate paths, trial labels, manifest.
- validation.py recomputes degrees/paths from sanitized triples before comparing
  methods. artifacts/validation.json now contains real metrics and individual ranks.
- data/raw/primekg.csv: 981,751,236 bytes, Dataverse file 6180620, MD5 verified
  against source metadata: aac8191d4fbc5bf09cdf8c3c78b4e75f.
- data/raw/trials.json: 2,615 completed/terminated trial records, 3 pages, 123 MiB.
- data/processed/training_edges.parquet: the ONLY allowed embedding input.
- data/processed/nodes.json: full node metadata. Exploratory edges.parquet also
  exists locally; it is UNSANITIZED and must never be used for training.
- Raw/processed files are Git-ignored. Hashes appear in artifacts/manifest.json.

## Real counts

- Source: 129,375 nodes / 8,100,498 reciprocal rows.
- Five Alzheimer disease nodes; explicitly non-Alzheimer entity excluded.
- Removed 146 target/drug rows (30 indication, 116 contraindication).
- Graph: 29,216 nodes / 503,232 pairs / 503,473 typed triples.
- Candidates: 1,801; 1,236 with paths; 159 outside graph retain zero scores.
- 576 eligible trials; 79 matched drugs; 48 in candidate universe, all in graph.
- Those 48 drugs match 83 unique trial IDs; 31 matched drugs outside eligibility;
  451 intervention names did not unambiguously match.

## Stage-2 results (completed)

| Method | recall@10 | recall@20 | query MRR | mean reciprocal held-out rank |
| --- | ---: | ---: | ---: | ---: |
| Random, 1000 seeds | 0.00541667 | 0.0108125 | 0.100826 | 0.00447279 |
| Popularity | 0 | 0 | 0.03125 | 0.00446734 |
| Path | 0.0833333 (4/48) | 0.104167 (5/48) | 0.2 | 0.0173213 |
| Embedding / combined | unavailable | unavailable | unavailable | unavailable |

- Real evaluation completed successfully, cached path scores/degrees reproduced.
- `python3 -m pytest -q`: 4 passed (leakage and numerical metrics).
- PyArrow printed sandbox CPU-cache sysctl warnings; parquet read and evaluation
  completed successfully. No failed tests or remaining data-access blocker.

## Decisions and caveats

- Universe: all drugs with a non-Alzheimer indication. Approval unverified;
  existing Alzheimer drugs can appear as rediscovery controls.
- Trial criteria: explicit Alzheimer condition, completed/terminated interventional
  treatment study, actual enrollment >0, drug assigned to an experimental arm.
- Exact normalized drug/alias match only; no fuzzy matches. Names can be missed.
- Delete ALL target/drug edges independent of trial labels. Retain only relations
  listed in graph.py; graph directions stay unknown, edge confidence unavailable.
- Fixed path score uses inverse sqrt of drug/intermediate degrees and length
  penalty, sums top 10; no label-based tuning. Evaluation is retrospective.
- MRR is reciprocal first relevant rank for ONE disease query. Also report the
  separately named mean reciprocal held-out rank across all 48 positives.
- Embedding/combined metrics unavailable until stage 5; never fabricate them.

## Next steps before mandatory checkpoint

1. Report checkpoint and WAIT. No UI/agent work until the user replies.
2. After explicit continuation: stage 3 cached UI, stage 4 evidence + citation tests,
   stage 5 sanitized embeddings + all baseline metrics, optional LINCS last.

```sh
PYTHONPATH=src python3 -m repurpose.cli prepare
PYTHONPATH=src python3 -m repurpose.cli validate
python3 -m pytest -q
git status --short
```
