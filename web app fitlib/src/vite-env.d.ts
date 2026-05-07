/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_STRIPE_PUBLIC_KEY?: string;
  readonly VITE_ALGOLIA_APP_ID?: string;
  readonly VITE_ALGOLIA_SEARCH_KEY?: string;
  readonly VITE_ALGOLIA_INDEX_NAME?: string;
  readonly VITE_ADMIN_EMAILS?: string;
}
