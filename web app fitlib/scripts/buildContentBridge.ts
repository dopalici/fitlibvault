import fs from 'fs';
import path from 'path';
import { extractVault } from './extractVault';
import { buildCards } from './buildClozeCards';
import { NodeData, NodeSummary } from '../src/types';

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
  try {
    const cardStats = buildCards();
    const coverage = cardStats.nodes === 0
      ? 0
      : (cardStats.nodes - cardStats.zeroCardNodes.length) / cardStats.nodes;
    console.log(
      `✅ Cloze cards: ${cardStats.cards} cards across ${cardStats.nodes} nodes (${(coverage * 100).toFixed(1)}% coverage)`
    );
  } catch (err) {
    console.warn(`⚠️  Cloze card generation skipped:`, err instanceof Error ? err.message : err);
  }
}

buildContentBridge().catch((error) => {
  console.error('❌ Failed to build content bridge:', error instanceof Error ? error.message : error);
  process.exit(1);
});
