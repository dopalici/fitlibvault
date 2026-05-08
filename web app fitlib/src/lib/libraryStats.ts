/**
 * Live, content-bridge-backed statistics for the Dashboard and the
 * Transparency page.
 *
 * Everything here reads from the static `public/content/*.json` files written
 * by `npm run content:build` — no Firestore round-trip required. That keeps
 * the dashboard fast offline, makes the Transparency page genuinely a snapshot
 * of *the library you're looking at* rather than aspirational marketing copy,
 * and means a fresh `npm run dev` shows the real numbers immediately.
 */

interface SeriesBreakdown {
  series: string;
  total: number;
  totalLinks: number;
  averageCredibility: number;
}

interface EvidenceQualityBreakdown {
  High: number;
  Medium: number;
  Low: number;
  Unknown: number;
}

export interface LibraryStats {
  generatedAt: string;
  totalNodes: number;
  totalCitations: number;
  averageCredibility: number;
  totalLinks: number;
  series: SeriesBreakdown[];
  totalCards: number;
  cardCoverage: number;
  evidenceQuality: EvidenceQualityBreakdown;
  totalEvidenceEntries: number;
  brokenWikilinks?: number;
}

const STATS_PATH = '/content/stats.json';
const STATS_CACHE_KEY = 'fitlib.libraryStats.v1';

let cachedStats: LibraryStats | null = null;
let inflight: Promise<LibraryStats | null> | null = null;

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path);
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

export async function loadLibraryStats(force = false): Promise<LibraryStats | null> {
  if (!force && cachedStats) return cachedStats;
  if (inflight) return inflight;

  inflight = (async () => {
    const stats = await fetchJson<LibraryStats>(STATS_PATH);

    if (!stats) {
      // Fall back to a previously-saved snapshot so the dashboard isn't blank
      // when the dev server briefly returns a 404 mid-rebuild.
      try {
        if (typeof window !== 'undefined') {
          const cached = window.localStorage.getItem(STATS_CACHE_KEY);
          if (cached) return JSON.parse(cached) as LibraryStats;
        }
      } catch {
        /* ignore */
      }
      return null;
    }

    cachedStats = stats;
    try {
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(STATS_CACHE_KEY, JSON.stringify(stats));
      }
    } catch {
      /* quota — fine */
    }
    return stats;
  })();

  try {
    return await inflight;
  } finally {
    inflight = null;
  }
}

/** Human label for a series id so the UI doesn't have to keep redoing the map. */
export function seriesLabel(series: string): string {
  switch (series) {
    case 'A':
      return 'Foundational';
    case 'B':
      return 'Resistance Training';
    case 'C':
      return 'Nutrition & Diet';
    case 'D':
      return 'Weight Management';
    case 'E':
      return 'Cardiovascular';
    case 'F':
      return 'Performance Factors';
    case 'Other':
      return 'Other / Indices';
    default:
      return `Series ${series}`;
  }
}

/** Tailwind tone for series — keeps a single source of truth across pages. */
export function seriesTone(series: string): { dot: string; text: string; bg: string } {
  switch (series) {
    case 'A':
      return { dot: 'bg-blue-500', text: 'text-blue-400', bg: 'bg-blue-500/10' };
    case 'B':
      return { dot: 'bg-emerald-500', text: 'text-emerald-400', bg: 'bg-emerald-500/10' };
    case 'C':
      return { dot: 'bg-orange-500', text: 'text-orange-400', bg: 'bg-orange-500/10' };
    case 'D':
      return { dot: 'bg-purple-500', text: 'text-purple-400', bg: 'bg-purple-500/10' };
    case 'E':
      return { dot: 'bg-rose-500', text: 'text-rose-400', bg: 'bg-rose-500/10' };
    case 'F':
      return { dot: 'bg-amber-500', text: 'text-amber-400', bg: 'bg-amber-500/10' };
    default:
      return { dot: 'bg-slate-500', text: 'text-slate-300', bg: 'bg-slate-500/10' };
  }
}
