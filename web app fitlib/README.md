# FitLib — Web App

Last reviewed: 2026-05-08

The production web client for FitLib's evidence-based fitness knowledge graph. React 19 SPA over an Express API, content sourced from a static JSON bridge generated from the Obsidian vault, learner state in Firestore + IndexedDB, billing through Stripe.

If you are new to the project, read `/Users/enes/fitlibvault-main/CAPABILITIES.md` first — it covers all three layers (vault, automation pipeline, web app). This README is the developer quickstart for the app layer only.

---

## What ships today

**Reader system**

- `StackedReader` — Andy-Matuschak-style horizontal panel stack; URL state is `?stack=A1,A2,…` for sharable / back-button-friendly navigation.
- `NoteReader` — section-aware rendering of the canonical note schema (Quick Takeaway, Key Points, Deep Dive, Research Evidence, Practical, Mistakes, Related).
- Wikilink interception — `[[link]]` opens the next stack column instead of navigating away.
- `NoteHoverCard` — Wikipedia-style hover preview, 180 ms enter delay.
- `EvidencePill` — High / Medium / Low / Unknown badges driven by parsed evidence metadata.
- Common-mistake callouts rendered as warning blocks.

**Graph view**

- `KnowledgeGraph` — D3 force simulation across the full link graph. Nodes coloured by series, zoom/pan, neighbour-dimming on hover, click to open in the reader.
- `AmbientGraph` — frozen-layout background graph cached in localStorage; near-zero CPU after first render.

**Active recall + spaced repetition**

- `clozeGen.ts` extracts cloze cards from Key Points using weighted heuristics (numeric ranges ×5, percentages ×4, acronyms ×3, noun phrases ×1). 508 cards across 678 nodes today.
- `srs.ts` schedules cards with FSRS-4 (`ts-fsrs`); review history persisted to IndexedDB via Dexie.
- `RecallSection` is the bottom-of-note "test yourself" block with grade buttons (Again / Hard / Good / Easy).
- Dashboard exposes due-card count, retention rate, and recently-reviewed widgets.

**Auth + paywall + payments**

- Firebase Auth (Google sign-in).
- Admin email allowlist (`VITE_ADMIN_EMAILS`) bypasses paywall.
- 5-node free tier; paywall modal triggers Stripe checkout (`stripeService.ts`).
- Stripe webhooks set `users/{uid}.premium` and revoke it on cancel.

**Content bridge**

- `extractVault.ts` walks the Obsidian vault, parses sections + wikilinks + citations, emits `fitlib_export.json`.
- `buildContentBridge.ts` produces `public/content/{index.json, nodes/<id>.json, series/<S>.json, stats.json}` and runs `buildClozeCards.ts` to emit `cards.json` + per-node `cards/<id>.json`.
- `importData.ts` mirrors the export into Firestore for backend reads.

**Server**

- Express 4 backend in `server.ts`. 9 routes covering health, nodes, user progress, checkout, subscription verification, analytics, and the Stripe webhook.
- Vite dev middleware in dev; static + SPA fallback in prod.

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19, react-router-dom 7, react-markdown, motion, tailwindcss v4 |
| Tooling | Vite 6, TypeScript 5.8, tsx |
| Visualisation | D3 7 (graph) |
| Backend | Express 4, firebase-admin 13 |
| Persistence | Firebase Firestore, IndexedDB (Dexie 4), localStorage |
| Search | Algolia (optional), in-memory fallback |
| Spaced repetition | `ts-fsrs` 5 |
| Payments | Stripe 22 |
| Deploy | Vercel (default), Docker (alt) |

---

## Local setup

```bash
cd "/Users/enes/fitlibvault-main/web app fitlib"
npm install
npm run dev          # starts Express + Vite on :3000
```

First-time content build:

```bash
npm run content:build
```

This is the only build step you need before `npm run dev` if `public/content/` is empty.

---

## Environment variables

See `docs/PRODUCTION_LAUNCH_CHECKLIST.md` § 1 for the full matrix with consumers, and the summary below for local dev.

Frontend (`.env.local`):

```bash
VITE_API_BASE_URL=http://localhost:3000
VITE_STRIPE_PUBLIC_KEY=pk_test_...
VITE_FIREBASE_API_KEY=...
VITE_FIREBASE_AUTH_DOMAIN=...
VITE_FIREBASE_PROJECT_ID=...
VITE_FIREBASE_STORAGE_BUCKET=...
VITE_FIREBASE_MESSAGING_SENDER_ID=...
VITE_FIREBASE_APP_ID=...
VITE_ADMIN_EMAILS=you@example.com           # optional, comma-separated
VITE_DEV_ADMIN=true                         # optional, dev-only bypass
VITE_ALGOLIA_APP_ID=...                     # optional; without these, in-memory search
VITE_ALGOLIA_SEARCH_KEY=...                 # optional
VITE_ALGOLIA_INDEX_NAME=...                 # optional
```

Backend (`.env`):

```bash
NODE_ENV=development
PORT=3000
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## NPM scripts

| Script | Purpose |
|---|---|
| `npm run dev` | Express + Vite dev server (hot reload) |
| `npm run content:build` | Regenerate `public/content/` from the vault |
| `npm run build` | `content:build` then `vite build` |
| `npm run preview` | Serve the production build locally |
| `npm start` / `npm run start:prod` | Node (tsx) server in prod mode |
| `npm run lint` | `tsc --noEmit` — type check only |
| `npm test` | `lint` + `build` |
| `npm run check:launch` | `lint` + `build` + `/api/health` curl |
| `npm run docker:build` | `docker build -t fitlib:latest .` |
| `npm run docker:run` | `docker run -p 3000:3000 fitlib:latest` |
| `npm run docker:compose` | `docker-compose up -d` |
| `npm run health-check` | `curl -f http://localhost:3000/api/health` |
| `npm run clean` | `rm -rf dist` |

---

## Routes

```
/              Landing — live counters + pillars
/library       Library — Reader / Graph / Cards modes, paywall
/dashboard     Dashboard — due cards, recents, favourites, FSRS stats
/about         About — evidence-quality breakdown, transparency
```

API (`server.ts`):

```
GET  /api/health
GET  /api/nodes
GET  /api/nodes/:id
GET  /api/users/:userId/progress
POST /api/users/:userId/progress
POST /api/create-checkout-session
GET  /api/check-subscription
GET  /api/analytics/:userId
POST /api/stripe/webhook
```

---

## Where things live

| Area | Path |
|---|---|
| Pages | `src/pages/` (Landing, Library, Dashboard, About) |
| Components | `src/components/` (NoteReader, StackedReader, KnowledgeGraph, AmbientGraph, RecallSection, NoteHoverCard, LibraryExplorer, PremiumPaywall, NoteSidekick, DataImporter, EvidencePill, CitationCard) |
| Services | `src/services/nodeService.ts` (single read service over content bridge + Firestore fallback) |
| Lib utilities | `src/lib/` (noteSchema, clozeGen, srs, noteStack, algoliaService, firebase, stripeService, env, admin, theme, libraryStats, wikilinks, favorites, recentlyViewed, backlinks, seed) |
| Static data | `src/data/mockNodes.ts` (dev fallback) |
| Types | `src/types.ts` |
| Build scripts | `scripts/` (extractVault, buildContentBridge, buildClozeCards, importData) |
| Backend | `server.ts` |
| Generated content | `public/content/` (gitignored — regenerate with `npm run content:build`) |
| Firestore rules | `firestore.rules` |
| Build config | `vite.config.ts`, `tsconfig.json`, `Dockerfile`, `docker-compose.yml`, `vercel.json` |

---

## Documentation map

Operating documents are in `docs/`. Read in this order:

1. `docs/README.md` — index + first-week playbook.
2. `docs/SOP_KNOWLEDGE_READER_SYSTEMS.md` — how the reader / FSRS / cards work in operation.
3. `docs/SOP_CONTENT.md` — how to author or improve a note.
4. `docs/SOP_EXTRACTION.md` — how the vault → JSON bridge works.
5. `docs/PRODUCTION_LAUNCH_CHECKLIST.md` — preflight before deploy.
6. `docs/VERCEL_DEPLOYMENT_CHECKLIST.md` — Vercel-specific steps.
7. `docs/DEVELOPMENT_PROGRESS.md` — what is shipped vs in progress.
8. `docs/ROADMAP.md` and `docs/KPIs.md` — direction and metrics.
9. `INTEGRATION.md` — wiring guide for the reader / SRS / cards modules (mostly historical now that they are landed).

For the bigger picture covering the automation pipeline and content vault, see `/Users/enes/fitlibvault-main/CAPABILITIES.md`.
