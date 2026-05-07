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
  'organized_library/automation_tools',
]);

interface MarkdownCandidate {
  filePath: string;
  relativePath: string;
  content: string;
  title: string;
  id: string;
}

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

function extractExplicitId(content: string): string | null {
  const idMatch = content.match(/\*\*ID:\*\*\s*([^\n*]+?)(?:\s+\*\*Created:|\s*$)/i);
  if (!idMatch?.[1]) return null;
  const normalized = idMatch[1]
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^A-Za-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toUpperCase();
  return normalized || null;
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

function deriveNodeId(relativePath: string, title: string, content?: string): string {
  const explicitId = content ? extractExplicitId(content) : null;
  if (explicitId) {
    return explicitId;
  }

  const filename = path.basename(relativePath, '.md');
  const dottedIdMatch = filename.match(/^([A-Z]{1,4}-?\d+(?:\.\d+)+)\b/i);
  if (dottedIdMatch) {
    return dottedIdMatch[1].toUpperCase().replace(/\./g, '-');
  }

  const idMatch = filename.match(/^([A-Z]{1,4}-?\d+)\b/i);
  if (idMatch) {
    return idMatch[1].toUpperCase().replace(/\./g, '-');
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

// Section headings used by the structured note schema. These are *not* note
// titles, even though they sit at the same markdown level — the title-fix
// must look past them.
const STRUCTURED_SECTION_HEADINGS = new Set([
  'quick takeaway',
  'key points',
  'deep dive',
  'research evidence',
  'evidence',
  'practical applications',
  'common mistakes',
  'related concepts',
  'update log',
  'note',
]);

function findStructuredTitle(content: string): string | null {
  // Prefer the first level-3 heading (canonical: `### Title`). Fall back to
  // the level-1 heading. In both cases, skip headings whose normalized text
  // matches a known section name.
  const lines = content.split('\n');
  // Pass 1: level 3
  for (const line of lines) {
    const m = line.match(/^###\s+(.+?)\s*$/);
    if (!m) continue;
    const text = m[1].trim();
    const stripped = text.replace(/^[A-Z]{1,4}-?\d+(?:\.\d+)*\.\s*/, '').toLowerCase();
    if (STRUCTURED_SECTION_HEADINGS.has(stripped)) continue;
    if (STRUCTURED_SECTION_HEADINGS.has(text.toLowerCase())) continue;
    return text;
  }
  // Pass 2: level 2 (some rewrites use `##` as the title bar)
  for (const line of lines) {
    const m = line.match(/^##\s+(.+?)\s*$/);
    if (!m) continue;
    const text = m[1].trim();
    if (STRUCTURED_SECTION_HEADINGS.has(text.toLowerCase())) continue;
    return text;
  }
  return null;
}

function isBackupPath(relativePath: string): boolean {
  return relativePath.includes('original_backup/') || /_backup\.md$/i.test(relativePath);
}

function isRewrittenPath(relativePath: string): boolean {
  const filename = path.basename(relativePath);
  return relativePath.includes('/rewritten_') || filename.startsWith('rewritten_');
}

function candidatePriority(relativePath: string): number {
  // Prefer canonical vault files (repo root) over organized/archive copies.
  if (relativePath.startsWith('organized_library/')) return 10;
  return 100;
}

function normalizeLeadingIdTitle(title: string): string {
  return title
    .replace(/^([A-Z]{1,4}-?\d+)\.\s+/i, '$1 ')
    .replace(/\s+/g, ' ')
    .trim()
    .toLowerCase();
}

function hasDottedIdPrefix(value: string): boolean {
  return /^([A-Z]{1,4}-?\d+)\.\s+/i.test(value);
}

function shouldReplaceCandidate(nextDoc: MarkdownCandidate, currentDoc: MarkdownCandidate): boolean {
  const nextPriority = candidatePriority(nextDoc.relativePath);
  const currentPriority = candidatePriority(currentDoc.relativePath);
  if (nextPriority !== currentPriority) return nextPriority > currentPriority;

  // If these are punctuation-only title variants, prefer dotted canonical style ("B15. ...").
  const nextNormalizedTitle = normalizeLeadingIdTitle(nextDoc.title);
  const currentNormalizedTitle = normalizeLeadingIdTitle(currentDoc.title);
  if (nextNormalizedTitle === currentNormalizedTitle) {
    const nextIsDotted = hasDottedIdPrefix(nextDoc.title);
    const currentIsDotted = hasDottedIdPrefix(currentDoc.title);
    if (nextIsDotted !== currentIsDotted) return nextIsDotted;
  }

  if (nextDoc.relativePath.length !== currentDoc.relativePath.length) {
    return nextDoc.relativePath.length < currentDoc.relativePath.length;
  }
  return nextDoc.relativePath < currentDoc.relativePath;
}

export async function extractVault(): Promise<ExportData> {
  if (!fs.existsSync(VAULT_PATH)) {
    throw new Error(`Vault not found at ${VAULT_PATH}`);
  }

  const markdownPaths = collectMarkdownFiles(VAULT_PATH);
  const candidates: MarkdownCandidate[] = [];
  const ignoredBackupOrRewritten: string[] = [];

  markdownPaths.forEach((filePath) => {
    const relativePath = path.relative(VAULT_PATH, filePath).replace(/\\/g, '/');
    if (isBackupPath(relativePath) || isRewrittenPath(relativePath)) {
      ignoredBackupOrRewritten.push(relativePath);
      return;
    }

    const content = fs.readFileSync(filePath, 'utf-8');
    const filename = path.basename(filePath, '.md');

    // Prefer the title declared inside the rewritten note body when the file
    // also carries an explicit `**ID:**` line (the rewritten-vault variant).
    // Without this, files whose filename was never updated after a rewrite
    // surface a stale title in the reader (e.g. "A58. Training Monitoring"
    // showing instead of "A58. Cellular Autophagy Enhancement").
    //
    // Important: the structured schema lays out section headings as `##`
    // ("Quick Takeaway", "Key Points", etc.). We must skip those when looking
    // for the title — otherwise an `## Quick Takeaway` ends up as the note's
    // displayed name. Look only at the highest-level heading present (#, then
    // ###) and reject section names explicitly.
    const explicitId = extractExplicitId(content);
    const structuredTitle = explicitId ? findStructuredTitle(content) : null;
    const heading = content.match(/^#\s+(.+)$/m)?.[1]?.trim();
    const title = structuredTitle || heading || filename;
    const id = deriveNodeId(relativePath, title, content);
    candidates.push({ filePath, relativePath, content, title, id });
  });

  const preferredDocsById = new Map<string, MarkdownCandidate>();
  const overriddenDocs: Array<{ id: string; preferred: string; discarded: string }> = [];

  candidates.forEach((candidate) => {
    const existing = preferredDocsById.get(candidate.id);
    if (!existing) {
      preferredDocsById.set(candidate.id, candidate);
      return;
    }

    if (shouldReplaceCandidate(candidate, existing)) {
      overriddenDocs.push({
        id: candidate.id,
        preferred: candidate.relativePath,
        discarded: existing.relativePath,
      });
      preferredDocsById.set(candidate.id, candidate);
      return;
    }

    overriddenDocs.push({
      id: candidate.id,
      preferred: existing.relativePath,
      discarded: candidate.relativePath,
    });
  });

  // Title-based dedupe: when two distinct ids end up with the same display
  // title (e.g. `A3-MACRONUTRIENTS` from the rewritten file and `A3` from a
  // legacy filename-only copy), prefer the one whose source carried an
  // explicit `**ID:**` line — that's the canonical rewrite. The discarded
  // copy still contributes its filename to the alias map below so any
  // wikilink that targeted the legacy slug still resolves.
  const docsByTitle = new Map<string, MarkdownCandidate>();
  const titleAliasFallback: MarkdownCandidate[] = [];
  preferredDocsById.forEach((candidate) => {
    const titleKey = candidate.title.trim().toLowerCase();
    const existing = docsByTitle.get(titleKey);
    if (!existing) {
      docsByTitle.set(titleKey, candidate);
      return;
    }
    const existingHasId = Boolean(extractExplicitId(existing.content));
    const candidateHasId = Boolean(extractExplicitId(candidate.content));
    if (candidateHasId && !existingHasId) {
      titleAliasFallback.push(existing);
      docsByTitle.set(titleKey, candidate);
    } else {
      titleAliasFallback.push(candidate);
    }
  });

  const selectedDocs = Array.from(docsByTitle.values());
  const nodes: NodeData[] = [];
  const aliasToId = new Map<string, string>();
  const brokenLinks: Array<{ source_node: string; broken_link: string; issue: string }> = [];
  let totalWikilinks = 0;
  let resolvedWikilinks = 0;

  // First pass: build aliases and IDs for all markdown docs.
  const buildAliases = (doc: MarkdownCandidate): Set<string> => {
    const filename = path.basename(doc.filePath, '.md');
    const aliases = new Set([
      filename,
      doc.title,
      `${filename}.md`,
      `${doc.title}.md`,
      doc.relativePath,
      doc.relativePath.replace(/\.md$/i, ''),
    ]);
    const idPrefix = filename.match(/^([A-Z]{1,4}-?\d+)\b/i)?.[1];
    if (idPrefix) aliases.add(idPrefix.toUpperCase());
    return aliases;
  };

  selectedDocs.forEach((doc) => {
    buildAliases(doc).forEach((alias) => aliasToId.set(normalizeAlias(alias), doc.id));
  });

  // Title-dedupe fallback: ensure aliases of the discarded twin still point
  // to the kept id, otherwise wikilinks that used the legacy slug 404.
  titleAliasFallback.forEach((discarded) => {
    const survivorId = docsByTitle.get(discarded.title.trim().toLowerCase())?.id;
    if (!survivorId) return;
    buildAliases(discarded).forEach((alias) => {
      const key = normalizeAlias(alias);
      if (!aliasToId.has(key)) aliasToId.set(key, survivorId);
    });
  });

  // Second pass: extract content.
  selectedDocs.forEach((doc) => {
    const content = doc.content;
    const frontmatter = extractFrontmatter(content);
    const id = doc.id;
    const title = doc.title;
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
  if (ignoredBackupOrRewritten.length > 0) {
    console.log(`ℹ️ Ignored ${ignoredBackupOrRewritten.length} backup/rewritten markdown files`);
  }
  if (overriddenDocs.length > 0) {
    console.log(`ℹ️ Resolved ${overriddenDocs.length} duplicate ID candidates using canonical path priority`);
  }
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
