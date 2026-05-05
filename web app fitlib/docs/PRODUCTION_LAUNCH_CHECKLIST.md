# Production Launch Checklist

## Preflight Configuration

- Set all frontend vars from `.env.example` (`VITE_API_BASE_URL`, Stripe, Firebase, optional Algolia).
- Set backend secrets (`FIREBASE_SERVICE_ACCOUNT_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`).
- Confirm Stripe product price IDs in `src/lib/stripeService.ts` match your Stripe dashboard.

## Functional Smoke Tests

- Open `/library` and verify search updates results as you type.
- Filter by category and confirm server-driven results update.
- Open a node and verify citations render in the drawer.
- Confirm non-premium users hit paywall after free content limit.
- Start Stripe checkout and confirm redirect to Stripe-hosted checkout.

## Backend Contract Checks

- `GET /api/health` returns `status: ok`.
- `GET /api/nodes` returns list with expected fields.
- `GET /api/nodes/:id` returns node details plus `citations`.
- `GET /api/check-subscription?userId=<uid>` returns `premium` state.
- Stripe webhook endpoint is configured and signing secret matches environment.

## Quality Gates

- Run `npm run lint` with zero type errors.
- Run `npm run build` successfully.
- Run `npm run check:launch` while local API is up.
