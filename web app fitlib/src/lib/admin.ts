import type { User } from 'firebase/auth';
import { env } from './env';

/** True if the email matches an entry in VITE_ADMIN_EMAILS. */
export function isAdminEmail(email: string | null | undefined): boolean {
  if (!email) return false;
  const normalized = email.trim().toLowerCase();
  return env.adminEmails.includes(normalized);
}

/**
 * Resolve admin status for the current viewer.
 *
 * Returns true if **any** of:
 *   - We're running in Vite dev (`npm run dev`) — owner workstation.
 *   - The build was started with `VITE_DEV_ADMIN=true` — self-hosted owner.
 *   - The signed-in user's email is listed in `VITE_ADMIN_EMAILS`.
 *
 * The first two short-circuits also work when `user` is null, so the dev
 * server gives the owner full access without forcing a Google sign-in.
 */
export function isAdminUser(user?: User | null): boolean {
  if (env.devAdmin) return true;
  return isAdminEmail(user?.email);
}

/** True when paywall + free-tier limits should be bypassed for the current viewer. */
export function hasFullLibraryAccess(user?: User | null, premium = false): boolean {
  return isAdminUser(user) || premium;
}
