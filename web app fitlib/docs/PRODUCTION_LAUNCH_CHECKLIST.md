# Production Launch Checklist

Last reviewed: 2026-05-08

This checklist is the definitive preflight for shipping the FitLib SPA + API to production. Everything here is checkable against the codebase — every env var is consumed somewhere in `server.ts` or a `src/lib/*.ts` module, every smoke test maps to a route or component you can find in the source.

Run through it top to bottom. Do not skip steps marked **[blocker]**.

---

## 1. Environment variables

### 1.1 Frontend (Vite — set in Vercel project or `.env.local`)

| Var | Required | Consumed by | Notes |
|---|---|---|---|
| `VITE_API_BASE_URL` | **[blocker]** | `src/lib/env.ts` | Points the SPA at the Express API. Same-origin in single-deploy; cross-origin in split deploy. |
| `VITE_STRIPE_PUBLIC_KEY` | **[blocker]** | `src/lib/env.ts` → `stripeService.ts` | Publishable key for Stripe.js. |
| `VITE_FIREBASE_API_KEY` | **[blocker]** | `src/lib/firebase.ts` | Firebase web client init. |
| `VITE_FIREBASE_AUTH_DOMAIN` | **[blocker]** | same | |
| `VITE_FIREBASE_PROJECT_ID` | **[blocker]** | same | |
| `VITE_FIREBASE_STORAGE_BUCKET` | **[blocker]** | same | |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | **[blocker]** | same | |
| `VITE_FIREBASE_APP_ID` | **[blocker]** | same | |
| `VITE_ADMIN_EMAILS` | optional | `src/lib/env.ts` → `admin.ts` | Comma-separated allowlist. Bypasses paywall. |
| `VITE_DEV_ADMIN` | optional | `src/lib/admin.ts` | `true` enables admin bypass on the dev origin only. |
| `VITE_ALGOLIA_APP_ID` | optional | `src/lib/algoliaService.ts` | Without these three the app falls back to in-memory text search. |
| `VITE_ALGOLIA_SEARCH_KEY` | optional | same | |
| `VITE_ALGOLIA_INDEX_NAME` | optional | same | |
| `GEMINI_API_KEY` | unused | declared in `vite.config.ts` define-block | Reserved for future AI features. App does not call Gemini today. |

### 1.2 Backend (Node — set on Vercel function / Docker / your runtime)

| Var | Required | Consumed by | Notes |
|---|---|---|---|
| `PORT` | optional (default 3000) | `server.ts` | |
| `NODE_ENV` | **[blocker]** | `server.ts` | Set to `production` so the SPA fallback + static assets are wired. |
| `FIREBASE_SERVICE_ACCOUNT_KEY` | **[blocker]** | `server.ts` (firebase-admin init), `scripts/importData.ts` | Full JSON service-account string. |
| `STRIPE_SECRET_KEY` | **[blocker]** | `server.ts` | Server-side key. Never ship to client. |
| `STRIPE_WEBHOOK_SECRET` | **[blocker]** | `server.ts` `/api/stripe/webhook` | Required for signature verification. |

---

## 2. Stripe configuration

- [ ] Confirm both price IDs in `src/lib/stripeService.ts` `PREMIUM_TIER` (monthly + annual) match live products in the Stripe dashboard.
- [ ] In Stripe → Developers → Webhooks, add a new endpoint pointing at `https://<your-domain>/api/stripe/webhook`. Subscribe to `checkout.session.completed`, `customer.subscription.deleted`, `customer.subscription.paused`.
- [ ] Copy the new `whsec_...` into `STRIPE_WEBHOOK_SECRET`.
- [ ] Verify the webhook signature handler is reached: in Stripe dashboard, click "Send test event" → expect 200 in your function logs.

## 3. Firebase configuration

- [ ] `firestore.rules` deployed (`firebase deploy --only firestore:rules`). Confirm the email allowlist for `isAdmin()` matches your operator account.
- [ ] Service-account key JSON stored as `FIREBASE_SERVICE_ACCOUNT_KEY` (single-line, escaped).
- [ ] Confirm Firestore indexes exist for the queries server makes — none today require composite indexes; if you change `/api/nodes` filtering, review.
- [ ] Sign-in providers: Google enabled in Firebase Auth.

## 4. Content bridge

The SPA reads its content from `public/content/` JSON, regenerated at build time.

- [ ] `npm run content:build` succeeds with no errors.
- [ ] `public/content/index.json` exists and contains expected node count (currently 678).
- [ ] `public/content/stats.json` reflects the latest extract — totals, evidence quality, broken-wikilink count.
- [ ] `public/content/cards.json` exists. Card coverage today is ~41.7 %; this is expected for a heuristic generator and is not a blocker.

If the bridge is stale, run from `web app fitlib/`:

```bash
npm run content:build
```

If you also want the Firestore copy refreshed:

```bash
FITLIB_VAULT_PATH="/Users/enes/fitlibvault-main" npx tsx scripts/extractVault.ts
FIREBASE_SERVICE_ACCOUNT_KEY="$(cat firebase-service-account.json)" \
  npx tsx scripts/importData.ts
```

## 5. Functional smoke tests (manual, 10 min)

Run against the production URL with a real test user and an incognito window.

### 5.1 Anonymous

- [ ] `/` loads. Live counters show non-zero totals (nodes / citations / wikilinks / cards).
- [ ] `/about` loads. Evidence-quality breakdown matches `stats.json`.
- [ ] `/library` loads in Reader mode by default. Sidebar tree populates.
- [ ] Search input filters the sidebar live.
- [ ] First five nodes open without paywall. The sixth triggers the paywall.

### 5.2 Authenticated free user

- [ ] Google sign-in completes; user document is created in Firestore `users/{uid}`.
- [ ] Dashboard at `/dashboard` loads with empty state.
- [ ] Same 5-node paywall behaviour as anonymous.
- [ ] Recall block at the bottom of a focused note grades a card; review row appears in IndexedDB `fitlib-srs.reviews`.

### 5.3 Authenticated premium user

- [ ] Run a Stripe test checkout (test-mode price ID). Webhook fires; `users/{uid}.premium` flips to `true`.
- [ ] All paywall locks disappear.
- [ ] Cancellation event flips premium back to `false`.

### 5.4 Admin user

- [ ] Sign in with an email in `VITE_ADMIN_EMAILS`.
- [ ] Library shows the Admin badge in the sidebar.
- [ ] All locks bypassed without an active subscription.
- [ ] Dashboard exposes the `DataImporter` admin panel.

## 6. Backend contract checks

Run from a shell with `BASE=https://your-domain`:

```bash
curl -fsS "$BASE/api/health" | jq           # status: ok, firestore: connected
curl -fsS "$BASE/api/nodes?limit=1" | jq    # array of one node summary
curl -fsS "$BASE/api/nodes/A1-ENERGY-BALANCE" | jq | head -40
curl -fsS "$BASE/api/check-subscription?userId=$UID" | jq
```

Expected:

- [ ] `/api/health` returns `{"status":"ok","firestore":"connected", ...}` with HTTP 200.
- [ ] `/api/nodes` returns a 678-element list when no `limit` is passed (warning: response is large).
- [ ] `/api/nodes/:id` returns the node body plus the `citations` subcollection.
- [ ] `/api/check-subscription` returns `{ premium: true|false }`.
- [ ] `/api/analytics/:userId` returns completion rate, study streak, per-series progress.

## 7. Stripe webhook end-to-end

- [ ] In Stripe dashboard, create a test checkout session via the live price ID.
- [ ] Confirm the webhook endpoint receives `checkout.session.completed`.
- [ ] Confirm `users/{uid}.premium = true` after delivery.
- [ ] Trigger a manual `customer.subscription.deleted` test event. Confirm `premium = false`.

## 8. Quality gates

From `web app fitlib/`:

- [ ] `npm run lint` — zero TypeScript errors.
- [ ] `npm run build` — completes; `dist/` is populated.
- [ ] `npm run check:launch` — runs lint, build, and `/api/health` against a local server. Requires the server to be running first (`npm start` in another shell).

## 9. Deployment-platform checks

### Vercel (default)

- [ ] Vercel project root is set to `web app fitlib`.
- [ ] Build command: `npm run build`. Output: `dist`.
- [ ] All env vars from §1 set in Project Settings → Environment Variables.
- [ ] `vercel.json` SPA rewrite (`/(.*)` → `/index.html`) present.
- [ ] Detailed steps: `docs/VERCEL_DEPLOYMENT_CHECKLIST.md`.

### Docker (alternative)

- [ ] `docker build -t fitlib:latest .` builds clean.
- [ ] `docker run -p 3000:3000 --env-file .env.production fitlib:latest` starts and the container's healthcheck (`/api/health`) reports healthy.
- [ ] Optional: `docker-compose up -d` to run with the redis / prometheus profiles.

## 10. Rollback plan

- [ ] Previous deployment URL noted (Vercel keeps last N deploys; Docker users keep prior image tagged).
- [ ] If a webhook event causes a stuck subscription state: clear `users/{uid}.premium` directly in Firestore.
- [ ] If the content bridge is corrupted: re-run `npm run content:build` and redeploy. The bridge is regeneratable from the vault at any time.
- [ ] If a release introduces a Firestore-rules regression: redeploy the prior `firestore.rules` from git history (`firebase deploy --only firestore:rules`).

## 11. Post-launch monitoring (first 24h)

- [ ] Vercel function logs: no 5xx errors on `/api/*`.
- [ ] Stripe dashboard: events delivering, no webhook failures.
- [ ] Firebase console: auth signups, Firestore reads/writes within free-tier quota.
- [ ] Pin a tab to `/api/health` and refresh hourly the first day.

---

## Reference: routes registered in `server.ts`

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

If you add a route, add a smoke test in §5 or §6 of this file in the same PR.
