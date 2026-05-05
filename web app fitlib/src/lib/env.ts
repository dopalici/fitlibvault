const appEnv = import.meta.env;

export const env = {
  apiBaseUrl: appEnv.VITE_API_BASE_URL || '',
  stripePublicKey: appEnv.VITE_STRIPE_PUBLIC_KEY || '',
  algoliaAppId: appEnv.VITE_ALGOLIA_APP_ID || '',
  algoliaSearchKey: appEnv.VITE_ALGOLIA_SEARCH_KEY || '',
  algoliaIndexName: appEnv.VITE_ALGOLIA_INDEX_NAME || 'fitlib_nodes',
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
