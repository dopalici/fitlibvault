import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { NodeData, Citation } from '../src/types';

const VAULT_PATH = process.env.FITLIB_VAULT_PATH || path.resolve(process.cwd(), '..');
const OUTPUT_PATH = path.join(VAULT_PATH, 'fitlib_export.json');
const EXCLUDED_DIRS = new Set([
  '.git',
  'node_modules',
  '.cursor',
  'web app fitlib/dist',
]);

export interface VaultMetadata {
  version: string;
  exported_at: string;
  total_nodes: number;
  total_citations: number;
  broken_wikilinks: number;
  validation_warnings: number;
}

export interface ExportData {
  metadata: VaultMetadata;
  nodes: NodeData[];
  wikilink_validation: {
    total_wikilinks: number;
    resolved: number;
    broken: Array<{ source_node: string; broken_link: string; issue: string }>;
  };
}

function extractFrontmatter(content: string): { [key: string]: string } {
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) return {};
  
  const frontmatter: { [key: string]: string } = {};
  frontmatterMatch[1].split('\n').forEach(line => {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      frontmatter[key.trim()] = valueParts.join(':').trim();
    }
  });
  return frontmatter;
}

function extractSectionContent(content: string, sectionName: string): string {
  const regex = new RegExp(`## ${sectionName}\\n([\\s\\S]*?)(?=##|$)`, 'i');
  const match = content.match(regex);
  return match ? match[1].trim() : '';
}

function extractCitations(content: string): Citation[] {
  const citations: Citation[] = [];
  const citationBlocks = content.matchAll(/\*\*(.+?)\s+et\s+al\.\s+\((\d{4})\)\.\*\*[\s\S]*?(?=\*\*|$)/g);
  
  let citationId = 1;
  for (const match of citationBlocks) {
    const author = match[1];
    const year = parseInt(match[2]);
    const blockText = match[0];
    
    const titleMatch = blockText.match(/Title:\s*"([^"]+)"/i);
    const journalMatch = blockText.match(/Journal:\s*([^\n]+)/i);
    const typeMatch = blockText.match(/Type:\s*(Meta-Analysis|RCT|Systematic Review|Review)/i);
    const doiMatch = blockText.match(/DOI:\s*https?:\/\/doi\.org\/([^\n]+)/i);
    const qualityMatch = blockText.match(/Quality rating:\s*(High|Medium|Low)/i);
    
    citations.push({
      id: `c${citationId}`,
      type: (typeMatch?.[1] as any) || 'Review',
      credibilityScore: qualityMatch?.[1] === 'High' ? 0.95 : qualityMatch?.[1] === 'Medium' ? 0.75 : 0.5,
      author,
      year,
      title: titleMatch?.[1] || '',
      journal: journalMatch?.[1]?.trim() || '',
      doi: doiMatch ? `https://doi.org/${doiMatch[1]}` : undefined,
      qualityBreakdown: {
        studyDesign: qualityMatch?.[1] === 'High' ? 5 : 3,
        evidenceQuality: qualityMatch?.[1] === 'High' ? 5 : 3,
        biasRisk: 'Low',
        automationValidated: true,
      },
    });
    citationId++;
  }
  
  return citations;
}

function extractWikilinks(content: string): string[] {
  const wikilinks: string[] = [];
  const matches = content.matchAll(/\[\[([^\[\]]+)\]\]/g);

  for (const match of matches) {
    const rawTarget = match[1].split('|')[0].split('#')[0].trim();
    if (rawTarget) {
      wikilinks.push(rawTarget);
    }
  }

  return wikilinks;
}

function normalizeAlias(value: string): string {
  return value
    .toLowerCase()
    .replace(/\.md$/i, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function collectMarkdownFiles(dir: string, baseDir = dir): string[] {
  const files: string[] = [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    if (entry.name.startsWith('.')) continue;
    const absolutePath = path.join(dir, entry.name);
    const relativePath = path.relative(baseDir, absolutePath).replace(/\\/g, '/');

    if (entry.isDirectory()) {
      if (EXCLUDED_DIRS.has(relativePath) || EXCLUDED_DIRS.has(entry.name)) {
        continue;
      }
      files.push(...collectMarkdownFiles(absolutePath, baseDir));
      continue;
    }

    if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(absolutePath);
    }
  }

  return files;
}

function deriveNodeId(relativePath: string, title: string): string {
  const filename = path.basename(relativePath, '.md');
  const idMatch = filename.match(/^([A-Z]{1,4}-?\d+)\b/i);
  if (idMatch) {
    return idMatch[1].toUpperCase();
  }

  const slug = relativePath
    .replace(/\.md$/i, '')
    .toLowerCase()
    .replace(/[^a-z0-9/]+/g, '-')
    .replace(/\/+/g, '_')
    .replace(/-+/g, '-')
    .replace(/^[-_]+|[-_]+$/g, '');

  return slug || title.toLowerCase().replace(/[^a-z0-9]+/g, '-');
}

export async function extractVault(): Promise<ExportData> {
  if (!fs.existsSync(VAULT_PATH)) {
    throw new Error(`Vault not found at ${VAULT_PATH}`);
  }

  const markdownPaths = collectMarkdownFiles(VAULT_PATH);
  const nodes: NodeData[] = [];
  const aliasToId = new Map<string, string>();
  const brokenLinks: Array<{ source_node: string; broken_link: string; issue: string }> = [];
  let totalWikilinks = 0;
  let resolvedWikilinks = 0;

  // First pass: build aliases and IDs for all markdown docs.
  markdownPaths.forEach(filePath => {
    const relativePath = path.relative(VAULT_PATH, filePath).replace(/\\/g, '/');
    const raw = fs.readFileSync(filePath, 'utf-8');
    const filename = path.basename(filePath, '.md');
    const heading = raw.match(/^#\s+(.+)$/m)?.[1]?.trim();
    const title = heading || filename;
    const id = deriveNodeId(relativePath, title);

    const aliases = new Set([
      filename,
      title,
      `${filename}.md`,
      `${title}.md`,
      relativePath,
      relativePath.replace(/\.md$/i, ''),
    ]);

    const idPrefix = filename.match(/^([A-Z]{1,4}-?\d+)\b/i)?.[1];
    if (idPrefix) aliases.add(idPrefix.toUpperCase());

    aliases.forEach((alias) => aliasToId.set(normalizeAlias(alias), id));
  });

  // Second pass: extract content.
  markdownPaths.forEach(filePath => {
    const relativePath = path.relative(VAULT_PATH, filePath).replace(/\\/g, '/');
    const content = fs.readFileSync(filePath, 'utf-8');
    const frontmatter = extractFrontmatter(content);
    const fileTitle = path.basename(filePath, '.md');
    const heading = content.match(/^#\s+(.+)$/m)?.[1]?.trim();
    const title = heading || fileTitle;
    const id = deriveNodeId(relativePath, title);
    const seriesCandidate = (id.match(/^([A-Z])/i)?.[1] || 'Other').toUpperCase();
    const series = ['A', 'B', 'C', 'E'].includes(seriesCandidate)
      ? (seriesCandidate as 'A' | 'B' | 'C' | 'E')
      : 'Other';

    const fullContent = content.replace(/^---\n[\s\S]*?\n---\n?/m, '').trim() || `# ${title}`;
    const citations = extractCitations(content);
    const wikilinks = extractWikilinks(content);

    totalWikilinks += wikilinks.length;

    const resolvedLinks: string[] = [];
    wikilinks.forEach(wikilink => {
      const resolved = aliasToId.get(normalizeAlias(wikilink)) || null;
      if (resolved) {
        resolvedLinks.push(resolved);
        resolvedWikilinks++;
      } else {
        brokenLinks.push({
          source_node: id,
          broken_link: wikilink,
          issue: `Node "${wikilink}" not found in vault`,
        });
      }
    });

    const node: NodeData = {
      id,
      title,
      series: ['A', 'B', 'C', 'E'].includes(series) ? series : 'Other',
      content: fullContent,
      credibilityScore: citations.length > 0 
        ? citations.reduce((sum, c) => sum + c.credibilityScore, 0) / citations.length 
        : 0.5,
      citationCount: citations.length,
      citations,
      links: [...new Set(resolvedLinks)],
      tags: [
        ...new Set(
          extractSectionContent(content, 'Related Concepts')
            .split('[[')
            .filter(t => t.includes(']]'))
            .map(t => t.split(']]')[0].toLowerCase())
        ),
      ],
    };

    nodes.push(node);
  });

  const exportData: ExportData = {
    metadata: {
      version: '1.0',
      exported_at: new Date().toISOString(),
      total_nodes: nodes.length,
      total_citations: nodes.reduce((sum, n) => sum + n.citations.length, 0),
      broken_wikilinks: brokenLinks.length,
      validation_warnings: nodes.filter(n => n.citations.length < 8).length,
    },
    nodes,
    wikilink_validation: {
      total_wikilinks: totalWikilinks,
      resolved: resolvedWikilinks,
      broken: brokenLinks,
    },
  };

  // Create output directory
  const outputDir = path.dirname(OUTPUT_PATH);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(exportData, null, 2));
  console.log(`✅ Extracted ${nodes.length} nodes from Obsidian vault`);
  console.log(`✅ Total citations: ${exportData.metadata.total_citations}`);
  console.log(`✅ Wikilinks resolved: ${resolvedWikilinks}/${totalWikilinks}`);
  console.log(`✅ Export saved to ${OUTPUT_PATH}`);

  return exportData;
}

// Run extraction
const isMainModule =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

if (isMainModule) {
  extractVault().catch(err => {
    console.error('❌ Extraction failed:', err.message);
    process.exit(1);
  });
}

export default extractVault;
