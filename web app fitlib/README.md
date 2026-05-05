# FitLib Web App

FitLib is an evidence-based fitness knowledge platform with a cyberpunk interface, interactive knowledge graph, and premium subscription access.

## Tech Stack

- React + Vite + TypeScript
- Express server (`server.ts`)
- Firebase (Firestore + Auth)
- Stripe subscriptions
- Optional Algolia search index

## Local Setup

1. Install dependencies:
   - `npm install`
2. Create a local env file:
   - `cp .env.example .env.local`
3. Fill the required keys in `.env.local`:
   - Stripe (`VITE_STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`)
   - Firebase (`FIREBASE_SERVICE_ACCOUNT_KEY` and `VITE_FIREBASE_*` vars)
   - Optional Algolia (`VITE_ALGOLIA_*`)
4. Start the app:
   - `npm run dev`
5. Validate API health:
   - `npm run health-check`

## Scripts

- `npm run dev` - Start Express + Vite middleware in development.
- `npm run content:build` - Build static markdown content bridge (`public/content/*`) from vault notes.
- `npm run build` - Build content bridge and frontend bundle.
- `npm run start:prod` - Run server in production mode.
- `npm run lint` - Type-check with TypeScript.

## Vercel Deployment

- Vercel project root directory: `web app fitlib`
- Build command: `npm run build`
- Output directory: `dist`
- SPA routing is configured via `vercel.json`
- Step-by-step checklist: `docs/VERCEL_DEPLOYMENT_CHECKLIST.md`

## Core Paths

- Frontend: `src/`
- Backend API: `server.ts`
- Firestore rules: `firestore.rules`
- Docs and roadmap: `docs/`
