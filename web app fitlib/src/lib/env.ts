const appEnv = import.meta.env;

// Dev / owner override.
//
// We deliberately collapse the "demo / free / premium / admin" gating in two cases:
//   1. Vite dev mode (`npm run dev`) — local development should always have the
//      whole library and the admin tools (importer, seeder, etc.) available
//      without touching Stripe or signing in.
//   2. Explicit opt-in via `VITE_DEV_ADMIN=true` for self-hosted owner builds.
//
// In production builds without that flag, the original Stripe + admin-email
// flow still applies, so paying customers and real admins still work.
const devAdminFlag = (appEnv.VITE_DEV_ADMIN || '').toString().toLowerCase() === 'true';

export const env = {
  apiBaseUrl: appEnv.VITE_API_BASE_URL || '',
  stripePublicKey: appEnv.VITE_STRIPE_PUBLIC_KEY || '',
  algoliaAppId: appEnv.VITE_ALGOLIA_APP_ID || '',
  algoliaSearchKey: appEnv.VITE_ALGOLIA_SEARCH_KEY || '',
  algoliaIndexName: appEnv.VITE_ALGOLIA_INDEX_NAME || 'fitlib_nodes',
  adminEmails: (appEnv.VITE_ADMIN_EMAILS || '')
    .split(',')
    .map((email: string) => email.trim().toLowerCase())
    .filter(Boolean),
  isDev: Boolean(appEnv.DEV),
  /** True when the running build should treat the current viewer as a full admin. */
  devAdmin: Boolean(appEnv.DEV) || devAdminFlag,
};

export function getApiUrl(path: string): string {
  if (!env.apiBaseUrl) {
    return path;
  }

  const normalizedBase = env.apiBaseUrl.endsWith('/')
    ? env.apiBaseUrl.slice(0, -1)
    : env.apiBaseUrl;
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${normalizedBase}${normalizedPath}`;
}
