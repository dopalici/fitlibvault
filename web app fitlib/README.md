# FitLib Web App

FitLib is the production web client for the fitness knowledge graph, powered by structured markdown notes, evidence metadata, and learning-science review workflows.

This README is the fastest path to run, understand, and operate the app from your own perspective as owner/operator.

## What is now implemented

- Reader mode with layered graph + focused file panel (`StackedReader`)
- Section-aware note rendering (`Quick Takeaway`, `Key Points`, `Deep Dive`, `Evidence`, `Practical`, `Mistakes`, `Related`)
- Wikilink hover preview + stacked navigation via URL (`?stack=A1,A2,...`)
- Recall cards generated from key points (cloze format)
- FSRS spaced repetition scheduler with local IndexedDB storage
- Admin bypass access via env-configured email allowlist

## Tech Stack

- React + Vite + TypeScript
- Express server (`server.ts`)
- Firebase (Firestore + Auth)
- Stripe subscriptions
- Optional Algolia search index
- d3 graph rendering
- `ts-fsrs` + `dexie` for review scheduling and persistence

## Local setup

```bash
cd "/Users/enes/fitlibvault-main/web app fitlib"
npm install
npm run dev
```

If you have not yet installed the review dependencies:

```bash
npm install ts-fsrs dexie
```

## Environment variables

Base frontend variables:

- `VITE_API_BASE_URL`
- `VITE_STRIPE_PUBLIC_KEY`
- `VITE_ALGOLIA_APP_ID`
- `VITE_ALGOLIA_SEARCH_KEY`
- `VITE_ALGOLIA_INDEX_NAME`

Admin access:

- `VITE_ADMIN_EMAILS` (comma-separated)
  - Example: `VITE_ADMIN_EMAILS=you@example.com,cofounder@example.com`
  - Any logged-in user whose email is in this list gets full content access regardless of subscription state.

## Content pipeline scripts

- `npm run content:build`
  - Builds `public/content/index.json`
  - Builds `public/content/nodes/*.json`
  - Builds `public/content/series/*.json`
  - Builds `public/content/cards.json` + `public/content/cards/*.json`

- `npm run build`
  - Runs `content:build`, then builds frontend bundle

- `npm run lint`
  - Type-checks frontend code

## SOP documents (read these)

- System integration and wiring: `INTEGRATION.md`
- Full owner-operator SOP for all new systems: `docs/SOP_KNOWLEDGE_READER_SYSTEMS.md`
- Documentation index: `docs/README.md`

## Vercel deployment

- Project root directory: `web app fitlib`
- Build command: `npm run build`
- Output directory: `dist`
- SPA routing: `vercel.json`
- Checklist: `docs/VERCEL_DEPLOYMENT_CHECKLIST.md`

## Core paths

- Frontend: `src/`
- Backend API: `server.ts`
- Markdown content bridge builder: `scripts/buildContentBridge.ts`
- Cloze card builder: `scripts/buildClozeCards.ts`
- Docs: `docs/`
