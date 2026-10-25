# Final demo implementation plan

**Goal:** Finish the Alzheimer-only product with strict trial-label evaluation,
a static Parkinson generalization check, plain-language presentation and an
offline reproducible handoff. Latest user attachment supersedes prior stage gates.

**Architecture:** Keep rankings, graph guards, agents and verdicts unchanged.
Add audited label eligibility over cached source records and evaluate fixed ranks.
Serve strict/raw comparison artifacts, then a shared deterministic copy layer.
No new diseases, selectors, agents or paid calls. React/Vite + existing Python API.

## Phase ledger

- [x] Phase 0: 144 tests collected / 144 passed; branch 293e85e, demo-safe/main
  d35abee confirmed; 250 reachable Git blobs and 164 tracked files scanned with
  two local credential-value comparisons and provider/private-key patterns, no
  matches. Secret values never emitted. Gitleaks unavailable; this is a bounded
  scan, not a proof against every possible secret format.
- [x] Phase 1a: document all existing label filters and audit ten labels per disease;
  freeze a principle-based strict rule in README/docs before any strict metrics.
  This required preregistration commit is the explicit exception to one commit
  per phase. Do not inspect rank positions when adjudicating records.
- [x] Phase 1b: implement `strict_labels.py`, tests for patient/role/ambiguity
  exclusions; persist per-record decisions and evidence quotes; use the unchanged
  evaluator against fixed cached rankings; raw remains secondary. Stop immediately
  if Alzheimer strict labels <10 or evaluation becomes uninterpretable. Otherwise
  update validation API/UI and copy, with exact intervals and <30-family warning.
- [x] Phase 2: static Parkinson raw/strict table in validation only; no selector,
  candidates or evidence. Use the same artifact schema and label caveats.
- [x] Phase 3: shared plain-language data/templates, Simple/Detailed context,
  collapsible intro, keyboard tooltips and graph labels, evidence-specific card
  summaries; reading-level script and banned-copy lint. Same numeric artifacts
  in both modes; no agent/verdict changes. Browser-check all four pages.
- [x] Phase 4: actual local Git clone, README-only dependency install/build and
  offline checks; all requested idea queries; deployment config without deployment;
  DEMO/Q&A, HUMAN_CHECKS (10 claims + three human-AD families + five labels/disease),
  one-page README, screenshot set and deployment checklist.
- [ ] Phase 5: all tests/build/review/secret scan; merge only after passing; tag
  demo-final without moving demo-safe; final handoff and outcome table.

## Verification and scope decisions

Use test-first changes, targeted checks followed by full suite and frontend build.
Reuse cached data; no network needed for registry audit. Keep raw immutable
artifacts and score hashes. A stricter ground-truth set changes evaluation, not
rankings. Patient status and intervention role need affirmative registry evidence;
unclear records do not qualify. Symptoms in diagnosed patients may qualify; healthy
volunteers, probes, background agents and PK-only studies do not.

Optional sensitivity and Word exports are cut first and not needed for completion.
Phases stay ordered; no UI work before the strict-label hard-stop check. User
authorizes merge/tag only after final checks. Hosting credentials are not needed
to prepare deployment; never expose the live service publicly in this task.
