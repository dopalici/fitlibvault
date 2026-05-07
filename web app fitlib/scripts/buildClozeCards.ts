/**
 * Generates cloze cards from every node and emits:
 *   public/content/cards.json           \u2014 aggregate, for offline import / dev preview
 *   public/content/cards/{nodeId}.json  \u2014 per-node, for lazy fetch in the reader
 *
 * Determinism: card ids are FNV-1a hashes of (nodeId, index, span, point) so
 * regenerating cards across content rebuilds preserves SRS review history.
 *
 * Run as part of `npm run content:build` \u2014 the existing buildContentBridge.ts
 * has been updated to invoke this. You can also run standalone:
 *
 *   npx tsx scripts/buildClozeCards.ts
 */

import fs from 'fs';
import path from 'path';
import type { NodeData } from '../src/types';
import { parseNoteSections } from '../src/lib/noteSchema';
import { generateClozeCards, type ClozeCard } from '../src/lib/clozeGen';

const PROJECT_ROOT = process.cwd();
const CONTENT_ROOT = path.join(PROJECT_ROOT, 'public', 'content');
const NODES_ROOT = path.join(CONTENT_ROOT, 'nodes');
const CARDS_ROOT = path.join(CONTENT_ROOT, 'cards');

function ensureDir(dirPath: string) {
  if (!fs.existsSync(dirPath)) fs.mkdirSync(dirPath, { recursive: true });
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

function loadNodes(): NodeData[] {
  if (!fs.existsSync(NODES_ROOT)) {
    throw new Error(`Nodes directory missing: ${NODES_ROOT}\nRun \`npm run content:build\` first (or its underlying buildContentBridge).`);
  }
  const files = fs.readdirSync(NODES_ROOT).filter((f) => f.endsWith('.json'));
  const nodes: NodeData[] = [];
  for (const file of files) {
    try {
      const raw = fs.readFileSync(path.join(NODES_ROOT, file), 'utf8');
      const parsed = JSON.parse(raw) as NodeData;
      if (parsed && typeof parsed.content === 'string') nodes.push(parsed);
    } catch (e) {
      console.warn(`Skipping unreadable node ${file}:`, e instanceof Error ? e.message : e);
    }
  }
  return nodes;
}

function fileNameFor(nodeId: string): string {
  return `${encodeURIComponent(nodeId)}.json`;
}

interface CardStats {
  nodes: number;
  cards: number;
  perNode: { nodeId: string; cards: number }[];
  zeroCardNodes: string[];
}

function buildCards(): CardStats {
  ensureDir(CARDS_ROOT);
  clearDir(CARDS_ROOT);

  const nodes = loadNodes();
  const stats: CardStats = { nodes: nodes.length, cards: 0, perNode: [], zeroCardNodes: [] };
  const all: ClozeCard[] = [];

  for (const node of nodes) {
    const sections = parseNoteSections(node.content);
    const cards = generateClozeCards(node.id, sections);
    stats.cards += cards.length;
    stats.perNode.push({ nodeId: node.id, cards: cards.length });
    if (cards.length === 0) stats.zeroCardNodes.push(node.id);
    fs.writeFileSync(
      path.join(CARDS_ROOT, fileNameFor(node.id)),
      JSON.stringify({ nodeId: node.id, cards })
    );
    all.push(...cards);
  }

  fs.writeFileSync(
    path.join(CONTENT_ROOT, 'cards.json'),
    JSON.stringify({
      generatedAt: new Date().toISOString(),
      totalCards: all.length,
      cards: all,
    })
  );

  return stats;
}

function main() {
  const stats = buildCards();
  const coverage = stats.nodes === 0 ? 0 : (stats.nodes - stats.zeroCardNodes.length) / stats.nodes;
  console.log(
    [
      `\u2705 Generated ${stats.cards} cloze cards across ${stats.nodes} nodes`,
      `   Coverage: ${(coverage * 100).toFixed(1)}% (${stats.zeroCardNodes.length} nodes produced 0 cards)`,
    ].join('\n')
  );
  if (stats.zeroCardNodes.length > 0 && stats.zeroCardNodes.length <= 12) {
    console.log(`   Zero-card nodes: ${stats.zeroCardNodes.join(', ')}`);
  }
}

if (process.argv[1] && process.argv[1].endsWith('buildClozeCards.ts')) {
  try {
    main();
  } catch (err) {
    console.error('\u274c buildClozeCards failed:', err instanceof Error ? err.message : err);
    process.exit(1);
  }
}

export { buildCards };
