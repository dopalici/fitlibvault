import fs from 'fs';
import path from 'path';
import { extractVault } from './extractVault';
import { buildCards } from './buildClozeCards';
import { NodeData, NodeSummary } from '../src/types';
import { parseNoteSections, type EvidenceQuality } from '../src/lib/noteSchema';

const PROJECT_ROOT = process.cwd();
const CONTENT_ROOT = path.join(PROJECT_ROOT, 'public', 'content');
const NODES_ROOT = path.join(CONTENT_ROOT, 'nodes');
const SERIES_ROOT = path.join(CONTENT_ROOT, 'series');

function ensureDir(dirPath: string) {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
}

function clearDir(dirPath: string) {
  if (!fs.existsSync(dirPath)) return;
  for (const entry of fs.readdirSync(dirPath, { withFileTypes: true })) {
    const fullPath = path.join(dirPath, entry.name);
    if (entry.isDirectory()) {
      clearDir(fullPath);
      fs.rmdirSync(fullPath);
    } else {
      fs.unlinkSync(fullPath);
    }
  }
}

function normalizeExcerpt(markdown: string): string {
  return markdown
    .replace(/^#.*$/gm, '')
    .replace(/\[\[([^[\]]+)\]\]/g, '$1')
    .replace(/[*_`>#-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 220);
}

function toNodeSummary(node: NodeData): NodeSummary {
  return {
    id: node.id,
    title: node.title,
    series: node.series,
    credibilityScore: node.credibilityScore,
    citationCount: node.citationCount,
    links: node.links,
    tags: node.tags,
    excerpt: normalizeExcerpt(node.content),
  };
}

function toFileName(nodeId: string): string {
  return `${encodeURIComponent(nodeId)}.json`;
}

async function buildContentBridge() {
  ensureDir(CONTENT_ROOT);
  ensureDir(NODES_ROOT);
  ensureDir(SERIES_ROOT);
  clearDir(NODES_ROOT);
  clearDir(SERIES_ROOT);

  const exportData = await extractVault();
  const summaries: NodeSummary[] = exportData.nodes.map(toNodeSummary);

  const indexPayload = {
    generatedAt: new Date().toISOString(),
    metadata: exportData.metadata,
    totalNodes: summaries.length,
    nodes: summaries,
  };

  for (const node of exportData.nodes) {
    const nodePath = path.join(NODES_ROOT, toFileName(node.id));
    fs.writeFileSync(nodePath, JSON.stringify(node));
  }

  const bySeries = summaries.reduce<Record<string, NodeSummary[]>>((acc, summary) => {
    if (!acc[summary.series]) {
      acc[summary.series] = [];
    }
    acc[summary.series].push(summary);
    return acc;
  }, {});

  Object.entries(bySeries).forEach(([series, nodes]) => {
    fs.writeFileSync(path.join(SERIES_ROOT, `${series}.json`), JSON.stringify({
      generatedAt: indexPayload.generatedAt,
      series,
      totalNodes: nodes.length,
      nodes,
    }));
  });

  fs.writeFileSync(path.join(CONTENT_ROOT, 'index.json'), JSON.stringify(indexPayload));
  console.log(`✅ Content bridge generated with ${summaries.length} nodes`);
  console.log(`✅ Series chunks generated: ${Object.keys(bySeries).length}`);

  // Generate cloze cards for spaced-repetition recall.
  // Runs after node JSON files are written so it can read them back.
  let totalCards = 0;
  try {
    const cardStats = buildCards();
    totalCards = cardStats.cards;
    const coverage = cardStats.nodes === 0
      ? 0
      : (cardStats.nodes - cardStats.zeroCardNodes.length) / cardStats.nodes;
    console.log(
      `✅ Cloze cards: ${cardStats.cards} cards across ${cardStats.nodes} nodes (${(coverage * 100).toFixed(1)}% coverage)`
    );
  } catch (err) {
    console.warn(`⚠️  Cloze card generation skipped:`, err instanceof Error ? err.message : err);
  }

  writeStatsSnapshot(exportData.nodes, summaries, indexPayload.generatedAt, indexPayload.metadata, totalCards);
}

/**
 * A small precomputed digest used by the Landing and Transparency pages so
 * they don't have to download the full index (~500 KB) + cards aggregate
 * just to render top-line counts. Kept in sync with the LibraryStats shape
 * in src/lib/libraryStats.ts.
 */
function writeStatsSnapshot(
  nodes: NodeData[],
  summaries: NodeSummary[],
  generatedAt: string,
  metadata: unknown,
  totalCards: number
) {
  const seriesMap = new Map<string, { total: number; links: number; credSum: number }>();
  let credSum = 0;
  for (const summary of summaries) {
    const bucket = seriesMap.get(summary.series) || { total: 0, links: 0, credSum: 0 };
    bucket.total += 1;
    bucket.links += summary.links?.length || 0;
    bucket.credSum += summary.credibilityScore || 0;
    seriesMap.set(summary.series, bucket);
    credSum += summary.credibilityScore || 0;
  }
  const series = Array.from(seriesMap.entries())
    .map(([s, data]) => ({
      series: s,
      total: data.total,
      totalLinks: data.links,
      averageCredibility: data.total === 0 ? 0 : data.credSum / data.total,
    }))
    .sort((a, b) => b.total - a.total);
  const totalLinks = series.reduce((acc, s) => acc + s.totalLinks, 0);
  const averageCredibility = summaries.length === 0 ? 0 : credSum / summaries.length;

  // We have every node's markdown right here — compute the evidence-quality
  // breakdown across the *whole* library instead of the runtime 64-node sample.
  const evidenceQuality: Record<EvidenceQuality, number> = { High: 0, Medium: 0, Low: 0, Unknown: 0 };
  let totalEvidenceEntries = 0;
  let cardCoverageNodes = 0;
  // Reuse cards.json for the per-node coverage count so the snapshot doesn't
  // diverge from the same source of truth.
  const cardsPath = path.join(CONTENT_ROOT, 'cards.json');
  let cardsByNode = new Set<string>();
  try {
    if (fs.existsSync(cardsPath)) {
      const aggregate = JSON.parse(fs.readFileSync(cardsPath, 'utf-8')) as { cards?: { nodeId: string }[] };
      cardsByNode = new Set((aggregate.cards || []).map((c) => c.nodeId));
    }
  } catch {
    /* leave cardCoverage at 0 */
  }
  for (const node of nodes) {
    if (cardsByNode.has(node.id)) cardCoverageNodes += 1;
    if (typeof node.content !== 'string') continue;
    const sections = parseNoteSections(node.content);
    for (const entry of sections.evidence) {
      totalEvidenceEntries += 1;
      evidenceQuality[entry.quality] = (evidenceQuality[entry.quality] || 0) + 1;
    }
  }

  const meta = (metadata || {}) as { total_citations?: number; broken_wikilinks?: number };
  const stats = {
    generatedAt,
    totalNodes: summaries.length,
    totalCitations: meta.total_citations || 0,
    averageCredibility,
    totalLinks,
    series,
    totalCards,
    cardCoverage: summaries.length === 0 ? 0 : cardCoverageNodes / summaries.length,
    evidenceQuality,
    totalEvidenceEntries,
    brokenWikilinks: meta.broken_wikilinks,
  };
  fs.writeFileSync(path.join(CONTENT_ROOT, 'stats.json'), JSON.stringify(stats));
  console.log(`✅ Stats snapshot: ${summaries.length} nodes, ${totalEvidenceEntries} evidence entries`);
}

buildContentBridge().catch((error) => {
  console.error('❌ Failed to build content bridge:', error instanceof Error ? error.message : error);
  process.exit(1);
});
