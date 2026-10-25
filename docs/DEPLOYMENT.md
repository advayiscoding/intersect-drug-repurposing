# Deployment checklist

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

## What was and was not done

**Done:** a container image, a verified production run from a clean clone of the
tagged commit, offline and no-key verification, and the checklist below.

**Not done: no public deployment.** `docs/FINAL_PLAN.md` says never to expose the
live service publicly in this task, and no hosting credentials were requested or
used. The verification below is a real production-mode server serving the tagged
build, bound to loopback. Anyone deploying this must work through the pre-flight
list first — particularly the provider-side spend limit.

## Sizing (measured, not estimated)

| Thing | Value |
| --- | ---: |
| Peak resident for hot artifacts | **134 MB** |
| With uvicorn overhead | ~200 MB |
| Recommended instance | **512 MB** |
| Too small | 256 MB |
| Tracked repo | ~40 MB |
| Largest single load | `artifacts/explorer_details.json`, 16 MB JSON → ~73 MB resident |

Measured by loading each artifact and reading max RSS: 12 MB baseline → 85 MB after
`explorer_details.json` → 129 MB after the 107k-entry synonym map → 134 MB with the
rest. No sharding is needed at 512 MB. If you must fit 256 MB, shard
`explorer_details.json` per drug and read it from disk per request.

## Simplest option that fits

A single container on any 512 MB tier (Fly.io, Render, Railway, Cloud Run). There is
no database, no queue and no build step at request time — every page is a cached
artifact, so a single instance with no autoscaling is enough.

```sh
docker build -t intersect-workbench .
docker run --rm -p 8000:8000 intersect-workbench                 # cached only, no keys
docker run --rm -p 8000:8000 -e ANTHROPIC_API_KEY=... \
  -e REPURPOSE_OFFLINE=0 -e REPURPOSE_DAILY_LIVE_CAP=10 intersect-workbench
```

`REPURPOSE_OFFLINE=1` is the image default, so a container started with no
configuration cannot make a network call or spend anything.

## Pre-flight

- [ ] **Set a hard spend limit on the API key at the provider.** This is the only
      control a restart cannot defeat. Scope the key to a workspace with its own cap.
- [ ] Decide whether live agent runs are enabled at all. The demo is complete without
      them: 20 families and 28 common drug lookups are pre-computed and served as
      "cached". Leaving `REPURPOSE_OFFLINE=1` is the safe default.
- [ ] Set `REPURPOSE_DAILY_LIVE_CAP` for the audience size. The default of 40 is a
      brake, not a budget.
- [ ] **Mount a persistent volume for `data/cache/live_runs.json`** if the daily cap
      must actually hold. On an ephemeral disk the counter resets on every restart,
      making the effective ceiling the cap multiplied by the restart count.
- [ ] Confirm no key reaches the client: `GET /api/health` returns
      `live_agents_available` as a boolean and nothing else. A test asserts no
      endpoint response contains key material.
- [ ] Deploy from the **`demo-final`** tag, not from a branch tip.
- [ ] Re-run `python3 -m pytest -q` and `npm run build` against the tag.
- [ ] Check the four pages load and the Simple/Detailed switch works.
- [ ] Confirm the validation page leads with the **strict** result, not the raw one.
- [ ] Keep the URL unlisted unless someone has agreed to it being public. This is a
      hackathon research prototype that discusses medicines.

## Verified production run

From a clean `git clone` of the tagged commit, with the frontend built from
`package-lock.json` using npm's offline cache, served by uvicorn with
`ANTHROPIC_API_KEY` and `NCBI_API_KEY` removed from the environment and
`REPURPOSE_OFFLINE=1`:

| Check | Result |
| --- | --- |
| `pytest -q` in the clone | 187 passed |
| Frontend production build | passes |
| `/api/health` | 200, `live_agents_available: false` |
| `/api/overview`, `/api/gap-map` | 200 |
| All four pages | render, no error state |
| Simple and Detailed modes | both render on all four pages |
| 15 drug lookups | 12 resolved with paths, 1 no-path, 1 ambiguous chooser, 1 not-in-graph |
| Live agent runs | correctly unavailable, cached review shown |

With a key supplied and `REPURPOSE_OFFLINE=0`, `live_agents_available` becomes true
and the Re-run live control appears, subject to the session limit and the daily cap.
