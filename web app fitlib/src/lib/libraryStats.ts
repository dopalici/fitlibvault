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

import type { NodeData, NodeSummary } from '../types';
import { parseNoteSections, type EvidenceQuality } from './noteSchema';

interface ContentBridgeIndex {
  generatedAt: string;
  metadata?: {
    version?: string;
    exported_at?: string;
    total_nodes?: number;
    total_citations?: number;
    broken_wikilinks?: number;
    validation_warnings?: number;
  };
  totalNodes: number;
  nodes: NodeSummary[];
}

interface ClozeAggregate {
  generatedAt: string;
  totalCards: number;
  cards: { id: string; nodeId: string }[];
}

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

const INDEX_PATH = '/content/index.json';
const CARDS_PATH = '/content/cards.json';
const NODE_PATH = '/content/nodes';
const STATS_CACHE_KEY = 'fitlib.libraryStats.v1';

let cachedStats: LibraryStats | null = null;
let inflight: Promise<LibraryStats | null> | null = null;

async function fetchJson<T>(path: string): Promise<T | null> {
  try {
    const response = await fetch(path, { cache: 'no-cache' });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function summariseSeries(nodes: NodeSummary[]): SeriesBreakdown[] {
  const map = new Map<string, { total: number; links: number; credSum: number }>();
  nodes.forEach((node) => {
    const bucket = map.get(node.series) || { total: 0, links: 0, credSum: 0 };
    bucket.total += 1;
    bucket.links += node.links?.length || 0;
    bucket.credSum += node.credibilityScore || 0;
    map.set(node.series, bucket);
  });
  return Array.from(map.entries())
    .map(([series, data]) => ({
      series,
      total: data.total,
      totalLinks: data.links,
      averageCredibility: data.total === 0 ? 0 : data.credSum / data.total,
    }))
    .sort((a, b) => b.total - a.total);
}

/**
 * Sample evidence quality from a bounded set of nodes so the Transparency page
 * doesn't pull every node JSON on first paint. We hit ~64 spread across series
 * which is plenty to show a meaningful High/Med/Low distribution.
 */
async function sampleEvidenceQuality(
  nodes: NodeSummary[],
  maxSampleSize = 64
): Promise<{ quality: EvidenceQualityBreakdown; totalEvidenceEntries: number }> {
  const buckets: EvidenceQualityBreakdown = { High: 0, Medium: 0, Low: 0, Unknown: 0 };
  let totalEvidenceEntries = 0;
  if (nodes.length === 0) return { quality: buckets, totalEvidenceEntries };

  // Stratified pick: take an even share from each series so we don't oversample
  // whichever series happens to come first alphabetically.
  const bySeries = new Map<string, NodeSummary[]>();
  nodes.forEach((n) => {
    if (!bySeries.has(n.series)) bySeries.set(n.series, []);
    bySeries.get(n.series)!.push(n);
  });
  const perSeries = Math.max(2, Math.floor(maxSampleSize / Math.max(1, bySeries.size)));
  const sample: NodeSummary[] = [];
  bySeries.forEach((list) => sample.push(...list.slice(0, perSeries)));

  const results = await Promise.all(
    sample.map((summary) =>
      fetchJson<NodeData>(`${NODE_PATH}/${encodeURIComponent(summary.id)}.json`)
    )
  );

  results.forEach((node) => {
    if (!node || typeof node.content !== 'string') return;
    const sections = parseNoteSections(node.content);
    sections.evidence.forEach((entry) => {
      totalEvidenceEntries += 1;
      const key: EvidenceQuality = entry.quality;
      buckets[key] = (buckets[key] || 0) + 1;
    });
  });

  return { quality: buckets, totalEvidenceEntries };
}

export async function loadLibraryStats(force = false): Promise<LibraryStats | null> {
  if (!force && cachedStats) return cachedStats;
  if (inflight) return inflight;

  inflight = (async () => {
    const [index, cards] = await Promise.all([
      fetchJson<ContentBridgeIndex>(INDEX_PATH),
      fetchJson<ClozeAggregate>(CARDS_PATH),
    ]);

    if (!index) {
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

    const series = summariseSeries(index.nodes);
    const totalLinks = series.reduce((acc, s) => acc + s.totalLinks, 0);
    const averageCredibility =
      index.nodes.length === 0
        ? 0
        : index.nodes.reduce((acc, n) => acc + (n.credibilityScore || 0), 0) / index.nodes.length;

    const cardsWithNodes = new Set((cards?.cards || []).map((c) => c.nodeId));
    const cardCoverage =
      index.nodes.length === 0 ? 0 : cardsWithNodes.size / index.nodes.length;

    const { quality, totalEvidenceEntries } = await sampleEvidenceQuality(index.nodes);

    const stats: LibraryStats = {
      generatedAt: index.generatedAt,
      totalNodes: index.totalNodes,
      totalCitations: index.metadata?.total_citations || 0,
      averageCredibility,
      totalLinks,
      series,
      totalCards: cards?.totalCards || 0,
      cardCoverage,
      evidenceQuality: quality,
      totalEvidenceEntries,
      brokenWikilinks: index.metadata?.broken_wikilinks,
    };

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
