import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { NodeData, Citation } from '../src/types';

const VAULT_PATH = process.env.FITLIB_VAULT_PATH || path.resolve(process.cwd(), '..');
const OUTPUT_PATH = path.join(VAULT_PATH, 'fitlib_export.json');
const UNRESOLVED_WIKILINKS_REPORT_PATH = path.join(VAULT_PATH, 'wikilink_unresolved_report.json');
const EXCLUDED_DIRS = new Set([
  '.git',
  'node_modules',
  '.cursor',
  'web app fitlib/dist',
  'web app fitlib/docs',
  'organized_library/automation_tools',
]);

// organized_library contains automation assets, mirrors, and generated views.
// The runtime graph should be built from canonical vault-root notes only.
const EXCLUDE_ORGANIZED_LIBRARY = true;

interface MarkdownCandidate {
  filePath: string;
  relativePath: string;
  content: string;
  title: string;
  id: string;
  frontmatter: NoteFrontmatter;
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

interface NoteFrontmatter {
  id?: string;
  created?: string;
  updated?: string;
  section?: string;
  tags?: string[];
}

function extractFrontmatter(content: string): NoteFrontmatter {
  const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
  if (!frontmatterMatch) return {};
  
  const frontmatter: NoteFrontmatter = {};
  frontmatterMatch[1].split('\n').forEach(line => {
    const [key, ...valueParts] = line.split(':');
    if (key && valueParts.length > 0) {
      const normalizedKey = key.trim().toLowerCase();
      const rawValue = valueParts.join(':').trim();
      if (!rawValue) return;
      if (normalizedKey === 'tags') {
        const cleaned = rawValue.replace(/^\[/, '').replace(/\]$/, '');
        frontmatter.tags = cleaned
          .split(',')
          .map((item) => item.trim().replace(/^['"]|['"]$/g, ''))
          .filter(Boolean);
        return;
      }
      if (normalizedKey === 'id') frontmatter.id = rawValue;
      if (normalizedKey === 'created') frontmatter.created = rawValue;
      if (normalizedKey === 'updated') frontmatter.updated = rawValue;
      if (normalizedKey === 'section') frontmatter.section = rawValue;
    }
  });
  return frontmatter;
}

function extractSectionContent(content: string, sectionName: string): string {
  const regex = new RegExp(`## ${sectionName}\\n([\\s\\S]*?)(?=##|$)`, 'i');
  const match = content.match(regex);
  return match ? match[1].trim() : '';
}

function normalizeId(rawId: string): string {
  return rawId
    .trim()
    .replace(/\s+/g, '-')
    .replace(/[^A-Za-z0-9-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toUpperCase();
}

function extractExplicitId(content: string): string | null {
  const idMatch = content.match(/\*\*ID:\*\*\s*([^\n*]+?)(?:\s+\*\*Created:|\s*$)/i);
  if (!idMatch?.[1]) return null;
  const normalized = normalizeId(idMatch[1]);
  return normalized || null;
}

function extractExplicitDates(content: string): { created?: string; updated?: string } {
  const created = content.match(/\*\*Created:\*\*\s*([^(]+?)(?:\s*\(Updated:|\s*$)/im)?.[1]?.trim();
  const updated = content.match(/\(Updated:\s*([^)]+)\)/i)?.[1]?.trim();
  return { created, updated };
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

const LEGACY_WIKILINK_MIGRATIONS = new Map<string, string>(
  Object.entries({
    'G3. Training with Health Limitations & Chronic Conditions': 'G3-TRAINING-WITH-LIMITATIONS',
    'A35. Ground Reaction Force Analysis': 'A35-GROUND-REACTION-FORCE-ANALYSIS',
    'A50. Metabolic Flexibility Training': 'A56-METABOLIC-FLEXIBILITY-TRAINING',
    'A59. Telomere Length and Exercise': 'A52-TELOMERE-LENGTH-EXERCISE',
    'A66. Metabolic Flexibility Training': 'A62-METABOLIC-FLEXIBILITY-TRAINING',
    'A99. Advanced Biomarker Interpretation': 'C99',
    'B2. Protein Requirements': 'B2-PROTEIN-REQUIREMENTS',
    'C16. High-Quality Protein Sources': 'C16-HIGH-PROTEIN-DIETS',
    'C33. Anti-Inflammatory Foods/Diets': 'C33-ANTI-INFLAMMATORY-DIETS',
    'C8. Metabolic Adaptation (Adaptive Thermogenics)': 'C8-METABOLIC-ADAPTATION',
    'E4-CONCURRENT-TRAINING': 'E4',
    'L1-MOVEMENT-PATTERNS-FUNCTIONAL': 'L1-MOVEMENT-PATTERNS',
    'A67. Hormetic Stress Principles': 'A57-HORMETIC-STRESS-PRINCIPLES',
    'E. Cardiovascular & Endurance Training': 'e-cardiovascular-endurance-training',
    'proprioceptive training': 'F14',
    'functional movement patterns': 'L1-MOVEMENT-PATTERNS',
    'energy system development': 'A6-ENERGY-SYSTEMS',
    'training intensity zones': 'E13-HR-ZONE-TRAINING',
    'periodization principles': 'K2-PERIODIZATION-ADVANCED',
    'fatigue management strategies': 'F19',
    'C. Program Design': 'c',
    'M12. Training Recovery': 'M7-NUTRITION-RECOVERY',
    'Drop Sets': 'B73-MECHANICAL-DROP-SETS',
    'Progressive Overload': 'B1-PROGRESSIVE-OVERLOAD',
    'Recovery Strategies': 'm-recovery-strategies',
    'Hypertrophy Training': 'B3-HYPERTROPHY',
    'Training Volume': 'B5-TRAINING-VOLUME',
    'EXL-101 Cable Crunch': 'EXL-89-BW-CRUNCH',
    'FZA-2.1': 'F2',
    'L-CROSS-TRAINING-FUNCTIONAL-FITNESS': 'l-cross-training-and-functional-fitness',
    'G-VII-2-KINESIOLOGY-MOVEMENT': 'G-VII-2-KINESIOLOGY',
  }).map(([legacy, canonicalId]) => [normalizeAlias(legacy), canonicalId])
);

function stripCodeForParsing(content: string): string {
  const lines = content.split('\n');
  const stripped: string[] = [];
  let activeFence: { marker: '`' | '~'; length: number } | null = null;

  for (const line of lines) {
    const trimmed = line.replace(/^\s{0,3}/, '');
    const fenceMatch = trimmed.match(/^(`{3,}|~{3,})/);

    if (!activeFence) {
      if (fenceMatch) {
        activeFence = {
          marker: fenceMatch[1][0] as '`' | '~',
          length: fenceMatch[1].length,
        };
        stripped.push('');
        continue;
      }
      stripped.push(line);
      continue;
    }

    if (
      fenceMatch &&
      fenceMatch[1][0] === activeFence.marker &&
      fenceMatch[1].length >= activeFence.length
    ) {
      activeFence = null;
    }
    stripped.push('');
  }

  return stripped
    .join('\n')
    .replace(/(`+)([^`\n]+?)\1/g, (match) => ' '.repeat(match.length));
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
      const parts = relativePath.split('/');
      if (EXCLUDE_ORGANIZED_LIBRARY && parts.length >= 1 && parts[0] === 'organized_library') {
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

function deriveNodeId(relativePath: string, title: string, frontmatter?: NoteFrontmatter, content?: string): string {
  const frontmatterId = frontmatter?.id ? normalizeId(frontmatter.id) : null;
  if (frontmatterId) {
    return frontmatterId;
  }
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
    const parseContent = stripCodeForParsing(content);
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
    const frontmatter = extractFrontmatter(parseContent);
    const explicitId = frontmatter.id ? normalizeId(frontmatter.id) : extractExplicitId(parseContent);
    const structuredTitle = explicitId ? findStructuredTitle(parseContent) : null;
    const heading = parseContent.match(/^#\s+(.+)$/m)?.[1]?.trim();
    const title = structuredTitle || heading || filename;
    const id = deriveNodeId(relativePath, title, frontmatter, parseContent);
    candidates.push({ filePath, relativePath, content, title, id, frontmatter });
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
    const existingHasId = Boolean(
      existing.frontmatter.id || extractExplicitId(stripCodeForParsing(existing.content))
    );
    const candidateHasId = Boolean(
      candidate.frontmatter.id || extractExplicitId(stripCodeForParsing(candidate.content))
    );
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
  const numericPrefixToIds = new Map<string, Set<string>>();
  const brokenLinks: Array<{ source_node: string; broken_link: string; issue: string }> = [];
  const migrationHits = new Map<string, number>();
  const numericPrefixHits = new Map<string, number>();
  let totalWikilinks = 0;
  let resolvedWikilinks = 0;

  // First pass: build aliases and IDs for all markdown docs.
  const buildAliases = (doc: MarkdownCandidate): Set<string> => {
    const filename = path.basename(doc.filePath, '.md');
    const aliases = new Set([
      doc.id,
      `${doc.id}.md`,
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
    const numericPrefix = doc.id.match(/^([A-Z]{1,4}-?\d+)/i)?.[1]?.toUpperCase();
    if (numericPrefix) {
      const bucket = numericPrefixToIds.get(numericPrefix) || new Set<string>();
      bucket.add(doc.id);
      numericPrefixToIds.set(numericPrefix, bucket);
    }
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
    const parseContent = stripCodeForParsing(content);
    const frontmatter = doc.frontmatter;
    const fallbackDates = extractExplicitDates(parseContent);
    const id = doc.id;
    const title = doc.title;
    const sectionFromMetadata = frontmatter.section?.trim().toUpperCase();
    const seriesCandidate = (sectionFromMetadata?.[0] || id.match(/^([A-Z])/i)?.[1] || 'Other').toUpperCase();
    const series = ['A', 'B', 'C', 'E'].includes(seriesCandidate)
      ? (seriesCandidate as 'A' | 'B' | 'C' | 'E')
      : 'Other';

    const fullContent = content.replace(/^---\n[\s\S]*?\n---\n?/m, '').trim() || `# ${title}`;
    const citations = extractCitations(parseContent);
    const wikilinks = extractWikilinks(parseContent);

    totalWikilinks += wikilinks.length;

    const resolvedLinks: string[] = [];
    wikilinks.forEach(wikilink => {
      const wikilinkKey = normalizeAlias(wikilink);
      let resolved = aliasToId.get(wikilinkKey) || null;
      if (!resolved) {
        const migratedTargetId = LEGACY_WIKILINK_MIGRATIONS.get(wikilinkKey);
        if (migratedTargetId) {
          resolved = aliasToId.get(normalizeAlias(migratedTargetId)) || null;
          if (resolved) {
            migrationHits.set(wikilink, (migrationHits.get(wikilink) || 0) + 1);
          }
        }
      }
      if (!resolved) {
        const numericPrefix = wikilink.match(/^([A-Z]{1,4}-?\d+)(?:\.|\s|$)/i)?.[1]?.toUpperCase();
        if (numericPrefix) {
          const candidates = Array.from(numericPrefixToIds.get(numericPrefix) || []);
          if (candidates.length === 1) {
            resolved = candidates[0];
            numericPrefixHits.set(wikilink, (numericPrefixHits.get(wikilink) || 0) + 1);
          }
        }
      }
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
      created: frontmatter.created || fallbackDates.created,
      updated: frontmatter.updated || fallbackDates.updated,
      content: fullContent,
      credibilityScore: citations.length > 0 
        ? citations.reduce((sum, c) => sum + c.credibilityScore, 0) / citations.length 
        : 0.5,
      citationCount: citations.length,
      citations,
      links: [...new Set(resolvedLinks)],
      tags: [
        ...new Set([
          ...(frontmatter.tags || []).map((tag) => tag.toLowerCase()),
          ...extractSectionContent(parseContent, 'Related Concepts')
            .split('[[')
            .filter(t => t.includes(']]'))
            .map(t => t.split(']]')[0].toLowerCase()),
        ]),
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
  const brokenByTarget = brokenLinks.reduce<Record<string, number>>((acc, item) => {
    acc[item.broken_link] = (acc[item.broken_link] || 0) + 1;
    return acc;
  }, {});
  const unresolvedReport = {
    generated_at: new Date().toISOString(),
    summary: {
      total_wikilinks: totalWikilinks,
      resolved_wikilinks: resolvedWikilinks,
      unresolved_wikilinks: brokenLinks.length,
      unresolved_unique_targets: Object.keys(brokenByTarget).length,
    },
    unresolved_by_target: Object.entries(brokenByTarget)
      .sort((a, b) => b[1] - a[1])
      .map(([target, count]) => ({ target, count })),
  };
  fs.writeFileSync(UNRESOLVED_WIKILINKS_REPORT_PATH, JSON.stringify(unresolvedReport, null, 2));
  console.log(`✅ Extracted ${nodes.length} nodes from Obsidian vault`);
  console.log(`✅ Total citations: ${exportData.metadata.total_citations}`);
  console.log(`✅ Wikilinks resolved: ${resolvedWikilinks}/${totalWikilinks}`);
  if (ignoredBackupOrRewritten.length > 0) {
    console.log(`ℹ️ Ignored ${ignoredBackupOrRewritten.length} backup/rewritten markdown files`);
  }
  if (overriddenDocs.length > 0) {
    console.log(`ℹ️ Resolved ${overriddenDocs.length} duplicate ID candidates using canonical path priority`);
  }
  if (migrationHits.size > 0) {
    const totalMigrated = Array.from(migrationHits.values()).reduce((acc, count) => acc + count, 0);
    console.log(
      `ℹ️ Applied ${totalMigrated} legacy wikilink migrations across ${migrationHits.size} target labels`
    );
    Array.from(migrationHits.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .forEach(([label, count]) => {
        console.log(`   ↳ ${count}x [[${label}]]`);
      });
  }
  if (numericPrefixHits.size > 0) {
    const totalPrefixResolutions = Array.from(numericPrefixHits.values()).reduce((acc, count) => acc + count, 0);
    console.log(
      `ℹ️ Resolved ${totalPrefixResolutions} wikilinks via unique numeric-prefix fallback across ${numericPrefixHits.size} labels`
    );
    Array.from(numericPrefixHits.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .forEach(([label, count]) => {
        console.log(`   ↳ ${count}x [[${label}]]`);
      });
  }
  console.log(`✅ Export saved to ${OUTPUT_PATH}`);
  console.log(`✅ Unresolved wikilink report saved to ${UNRESOLVED_WIKILINKS_REPORT_PATH}`);

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
