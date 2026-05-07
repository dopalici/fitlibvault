/**
 * Local-first "recently viewed" trail used by the Dashboard's "Continue
 * Reading" panel.
 *
 * Why local instead of Firestore:
 *   - Reading the library shouldn't require an account in dev/owner mode.
 *   - The reader is the hot path; we don't want a network round-trip on
 *     every wikilink push.
 *   - The same data feeds the spaced-practice resumption: glance at the
 *     dashboard, see what you were last reading, jump straight back into
 *     the stacked reader at that note.
 *
 * Persists to localStorage so a refresh keeps your trail. We keep at most
 * `MAX_ENTRIES` and dedupe by nodeId — the most recent timestamp wins.
 */

const STORAGE_KEY = 'fitlib.recentlyViewed.v1';
const MAX_ENTRIES = 25;

export interface RecentNodeEntry {
  /** NodeData.id */
  id: string;
  title: string;
  series: string;
  /** Most recent open time, ms since epoch. */
  viewedAt: number;
  /** How many times we've recorded a view, lifetime. Useful for the dashboard. */
  views: number;
}

function safeRead(): RecentNodeEntry[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as RecentNodeEntry[];
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((e) => e && typeof e.id === 'string');
  } catch {
    return [];
  }
}

function safeWrite(entries: RecentNodeEntry[]): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  } catch {
    /* quota exceeded — drop the write silently */
  }
}

export function recordVisit(node: { id: string; title: string; series: string }): void {
  const now = Date.now();
  const current = safeRead();
  const existing = current.find((e) => e.id === node.id);
  const next: RecentNodeEntry = existing
    ? { ...existing, title: node.title, series: node.series, viewedAt: now, views: existing.views + 1 }
    : { id: node.id, title: node.title, series: node.series, viewedAt: now, views: 1 };
  const filtered = current.filter((e) => e.id !== node.id);
  const merged = [next, ...filtered].slice(0, MAX_ENTRIES);
  safeWrite(merged);
}

export function getRecentlyViewed(limit = 10): RecentNodeEntry[] {
  return safeRead()
    .sort((a, b) => b.viewedAt - a.viewedAt)
    .slice(0, limit);
}

export function clearRecentlyViewed(): void {
  safeWrite([]);
}

/**
 * Build a small wallclock-aware label like "5m ago", "2h ago", "yesterday".
 * Self-contained so the dashboard doesn't pull in a date-fns dep just for this.
 */
export function relativeTimeFrom(ts: number, now = Date.now()): string {
  const delta = Math.max(0, now - ts);
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (delta < minute) return 'just now';
  if (delta < hour) return `${Math.round(delta / minute)}m ago`;
  if (delta < day) return `${Math.round(delta / hour)}h ago`;
  if (delta < 2 * day) return 'yesterday';
  return `${Math.floor(delta / day)}d ago`;
}
