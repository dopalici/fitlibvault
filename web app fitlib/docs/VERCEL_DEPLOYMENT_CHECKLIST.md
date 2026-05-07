# Vercel Deployment Checklist (Functional-First)

This checklist prioritizes a fully functional FitLib app without monetization dependencies.

## 1) Local pre-check

Run from project root:

```bash
cd "/Users/enes/fitlibvault-main/web app fitlib"
npm install
npm run lint
npm run build
```

## 2) Create/Configure Vercel project

In Vercel dashboard:

- Import repository.
- Set **Root Directory** to `web app fitlib`.
- Framework: `Vite`.
- Build command: `npm run build`.
- Output directory: `dist`.

## 3) Set frontend environment variables

Set these in Vercel Project Settings -> Environment Variables:

- `VITE_API_BASE_URL` (leave empty for same-origin API; set to backend URL if external)
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

Optional:

- `VITE_ALGOLIA_APP_ID`
- `VITE_ALGOLIA_SEARCH_KEY`
- `VITE_ALGOLIA_INDEX_NAME`

## 4) Deploy

Push to your Git branch. Vercel auto-builds and deploys.

## 5) Post-deploy smoke tests

On the deployed URL:

- Home page loads.
- `/library` loads directly without 404.
- Search input updates results.
- Node drawer opens and renders markdown.
- Wikilink clicks navigate to linked nodes.

## 6) Firestore operational checklist

- Confirm Firestore rules are deployed.
- Confirm the `nodes` collection contains imported markdown nodes.
- Confirm `nodes/{nodeId}/citations` exists for sampled nodes.

## 7) Markdown pipeline refresh procedure

When vault content changes:

```bash
cd "/Users/enes/fitlibvault-main/web app fitlib"
npx tsx scripts/extractVault.ts
```

Then import to Firestore (requires server-side Firebase service account):

```bash
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}' npx tsx scripts/importData.ts
```
