# FitLib — Development Progress

Last updated: 2026-05-08

This is the current build snapshot. For aspirational targets see `ROADMAP.md`; for the metrics dashboard see `KPIs.md`; for a single-pane capability overview see `/Users/enes/fitlibvault-main/CAPABILITIES.md`.

---

## TL;DR

The app is functionally complete for its v1 surface area (Reader / Graph / Cards, paywall, FSRS, content bridge, Stripe, Firebase). The static content bridge has been refreshed (678 nodes, 985 citations, 5,568 wikilinks, 508 cloze cards). The automation pipeline ran 354 promotions on 2026-05-08. What is left is operational: production env config, Vercel deploy, Stripe live products, and content gap-filling for the F/G/H/I sections.

---

## Shipped (working, in `main`, verified against the codebase)

### Backend (`server.ts`)

- Express 4 + firebase-admin 13 with graceful init fallback when env vars are missing.
- Routes: `/api/health`, `/api/nodes`, `/api/nodes/:id`, `/api/users/:userId/progress` (GET + POST), `/api/create-checkout-session`, `/api/check-subscription`, `/api/analytics/:userId`, `/api/stripe/webhook`.
- Stripe API version pinned to `2026-04-22.dahlia`.
- CORS open by design; webhook handler uses `express.raw()` before `express.json()` to preserve signature.
- Vite middleware in dev; static + SPA fallback in prod.

### Frontend pages

| Route | File | Status |
|---|---|---|
| `/` | `pages/Landing.tsx` | Live counters from `stats.json`, two CTAs, four-pillar showcase |
| `/library` | `pages/Library.tsx` | Three modes (Reader / Graph / Cards), paywall, admin badge, search filter, sidebar tree |
| `/dashboard` | `pages/Dashboard.tsx` | Due-cards, recents, favourites, FSRS stats, Google sign-in, admin importer |
| `/about` | `pages/About.tsx` | Evidence-quality breakdown, series tiles, transparency view |

### Reader system

- `StackedReader.tsx` — multi-column reader with `?stack=` URL state.
- `NoteReader.tsx` — section-aware rendering driven by `parseNoteSections()`.
- `NoteHoverCard.tsx` — wikilink hover preview, 180 ms enter delay.
- `EvidencePill.tsx` — High / Medium / Low / Unknown badges.
- `CitationCard.tsx` — citation render block.
- Common-mistake callouts rendered in-line by `NoteReader`.

### Graph system

- `KnowledgeGraph.tsx` — D3 force layout with neighbour-dimming.
- `AmbientGraph.tsx` — frozen layout cached in localStorage; near-zero CPU after first paint.
- `NoteSidekick.tsx` — TOC + mini-graph sidebar.

### Active recall + FSRS

- `clozeGen.ts` — heuristic cloze generator from Key Points.
- `srs.ts` — `ts-fsrs` 5 + Dexie IndexedDB store (`fitlib-srs`); config `request_retention 0.9`, `maximum_interval 365`.
- `RecallSection.tsx` — input → grade → schedule UX.
- Aggregate stats consumed by Dashboard.

### Auth + payments

- Firebase Auth (Google sign-in) wired in `firebase.ts`, `Library.tsx`, `Dashboard.tsx`.
- Admin allowlist via `VITE_ADMIN_EMAILS` (comma-separated) in `admin.ts`.
- Stripe checkout via `stripeService.ts → POST /api/create-checkout-session`.
- Stripe webhook handler covers `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.paused`.
- `verifySubscription()` reads `users/{uid}.premium` through `/api/check-subscription`.
- 5-node free tier enforced in `Library.tsx`; admin / premium bypass it.

### Content bridge

- `extractVault.ts` — vault scan, wikilink + citation extraction, broken-link detection.
- `buildContentBridge.ts` — emits `index.json`, `nodes/<id>.json`, `series/<S>.json`, `stats.json`, then runs `buildClozeCards`.
- `buildClozeCards.ts` — emits `cards.json` + per-node `cards/<id>.json`. Stable IDs via FNV-1a hash so review history survives rebuilds.
- `importData.ts` — Firestore importer using batched 450-op writes.

### Persistence

- Firestore collections per `firestore.rules`: `nodes/{id}` + `nodes/{id}/citations/{cid}` (public read, admin write), `users/{uid}` (owner-write with field whitelist), `userProgress/{uid}` (owner-write), `admins/{aid}`.
- IndexedDB store `fitlib-srs` (cards + reviews tables).
- localStorage stores favourites, recently-viewed, ambient-graph layout, theme.

### Build / deploy

- Vite 6, Tailwind v4, TypeScript 5.8.
- Multi-stage Dockerfile (Node 18-alpine, non-root `fitlib:nodejs`, healthcheck on `/api/health`).
- `docker-compose.yml` with optional `redis` and `prometheus` profiles.
- `vercel.json` SPA rewrite.

---

## Latest content bridge stats (from `public/content/stats.json`, generated 2026-05-08T16:15Z)

| Metric | Value |
|---|---|
| Nodes | 678 |
| Citations | 985 |
| Wikilinks | 5,568 |
| Cards | 508 |
| Card coverage | 41.7 % |
| Average credibility | 0.50 |
| Evidence (High / Medium / Low / Unknown) | 1,109 / 260 / 0 / 42 |
| Broken wikilinks | 542 |
| Series shards | A (66), B (72), C (110), E (118), Other (312) |

`Other` rolls up D, F, G, H, I, J, K, L, M, N, O, P, Q, X — series shards for those letters are a pending bridge improvement.

Source vault (counted from `*.md` at the repo root):

| Section | Title | Subnotes |
|---|---|---|
| A | Foundational Concepts | 65 |
| B | Resistance Training | 70 |
| C | Nutrition & Diet | 106 |
| D | Weight Management | 3 |
| E | Cardio / Endurance | 15 |
| F | Optimal Performance | 34 |
| G | Special Populations | 16 |
| H | Body Composition | 3 |
| I | Hormones & Fitness | 3 |
| J | Technology | 10 |
| K | Elite Performance | 12 |
| L | Cross-Training | 4 |
| M | Recovery | 10 |
| N | Long-Term Development | 10 |
| O | Integrated Approaches | 8 |
| P | Ethics | 10 |
| Q | Key Topic Overviews | 8 |
| X | Sports-Specific | 30 |

---

## Wired but inactive

These exist in `package.json` / `firebase-blueprint.json` but are not used at runtime today:

- `@google/genai` — declared dependency, no source import. Reserved for future AI features.
- `redis` and `prometheus` Docker compose services — disabled by default profiles.
- `database.py` (Python) — async SQLite layer for citation/quality records, never exercised by the active pipeline.

## Optional, off by default

- **Algolia search** — `algoliaService.ts` is fully implemented but only activates when `VITE_ALGOLIA_APP_ID`, `VITE_ALGOLIA_SEARCH_KEY`, `VITE_ALGOLIA_INDEX_NAME` are all set. Without them the SPA uses in-memory text search over `index.json`.
- **`VITE_DEV_ADMIN`** — local-only admin bypass for development.

---

## Known issues / gaps

| Area | Issue | Severity |
|---|---|---|
| Content bridge | D and F nodes are folded into `Other` series shard | Cosmetic — UI still renders correctly |
| Wikilinks | 542 broken wikilinks at last extract | Operator follow-up via `interlink_validator.py` |
| Cloze cards | Coverage is 41.7 % because the heuristic only fires on numeric / acronym / quantitative key points | By design; could be improved with weight tuning in `clozeGen.ts` |
| FSRS | Review history is local-only (IndexedDB) — switching device loses progress | Roadmap: Firestore sync |
| Series breakdown | Series counters in `stats.json` show only A/B/C/E/Other — no D/F/G/etc. shard | Improvement: extend `buildContentBridge.ts` to enumerate every section |
| CI | No GitHub Actions / pre-commit. Lint and tests run manually | Recommended: add `npm test` on PR |
| Production hosting | Vercel project not provisioned yet (per `VERCEL_DEPLOYMENT_CHECKLIST.md`) | Blocker for live launch |
| Stripe live products | Test-mode price IDs only | Blocker for live launch |
| Firebase service account | Production service-account JSON not yet provisioned | Blocker for live launch |

---

## Active development focus (this week)

- Provision Vercel project, run first deploy, verify smoke tests in `PRODUCTION_LAUNCH_CHECKLIST.md`.
- Set Stripe live mode + update price IDs in `stripeService.ts`.
- Configure production Firebase service account.
- Iterate on remaining `interlink_audit_report.json` broken-link fixes via `staged_promotion.py`.

## Next 30 days

- Series shard improvement (D / F / G / H / I / J / K / L / M / N / O / P / Q / X).
- Add `/review` route — global due-card queue (skeleton already in `srs.ts::getDueCards`).
- First content gap pass for F (Optimal Performance Factors) — currently 34 notes, target ≥45.
- Add CI: `npm run lint && npm run build` + Python `pytest test_scripts/test_process_fitness_library_phase1.py` on every PR.

## Backlog (from `ROADMAP.md`)

- Firestore-backed FSRS sync.
- Mobile app (PWA first, native later).
- B2B API tier (Starter / Pro / Enterprise).
- "Explain it like I'm…" reading-level toggle.
- Pretest hooks above Quick Takeaway.

---

## Verification — how to check this status against the codebase

```bash
# Stats (the numbers in this doc)
cat "web app fitlib/public/content/stats.json" | jq

# Routes (cross-check the table above)
grep -E "app\.(get|post|put|delete)" "web app fitlib/server.ts"

# Active automation pipeline (reflected in CAPABILITIES.md)
cat organized_library/automation_tools/tools/SCRIPT_STATUS.md

# Latest promotions
wc -l organized_library/automation_tools/promotion_history.jsonl
tail -5 organized_library/automation_tools/promotion_history.jsonl | jq -r '.timestamp + "  " + .file'
```

Anything in this doc that disagrees with the codebase is a bug in the doc — open the issue or fix it directly.
