/**
 * Parses the FitLib structured note schema into typed sections.
 *
 * Authored notes follow this canonical shape (see /organized_library/.../rewritten_*.md):
 *
 *   ### {Title}
 *   **ID:** ...
 *   **Created:** ...
 *
 *   ## Quick Takeaway
 *   ...
 *
 *   ## Key Points
 *   - point 1
 *   - point 2
 *
 *   ## Deep Dive
 *   ...
 *
 *   ## Research Evidence
 *   **Author. (Year).** Title. *Journal*, ...
 *   - Key finding: ...
 *   - Study type: ...
 *   - Evidence quality: High|Medium|Low (...)
 *
 *   ## Practical Applications
 *   ...
 *
 *   ## Common Mistakes
 *   warn marker **bold-claim** - explanation
 *
 *   ## Related Concepts
 *   prose containing [[Other Note]] wiki-links
 *
 * Returning a typed object lets us drive evidence pills, cloze cards, hover
 * popovers, recall prompts and the table of contents off one source of truth
 * instead of re-parsing markdown three different ways.
 */

export type EvidenceQuality = 'High' | 'Medium' | 'Low' | 'Unknown';

export interface EvidenceEntry {
  /** Stable hash id for SRS card linking. */
  id: string;
  /** Raw bibliographic line, e.g. "Pontzer H, et al. (2021). Daily energy ..." */
  citation: string;
  /** First author + year if extractable. */
  authorYear?: string;
  /** "Key finding: ..." line content if present. */
  keyFinding?: string;
  /** "Study type: ..." line content if present. */
  studyType?: string;
  /** Parsed evidence quality flag. */
  quality: EvidenceQuality;
  /** Free-text qualifier inside the parens after High/Medium/Low. */
  qualityNote?: string;
}

export interface CommonMistake {
  /** Bold lead-in, e.g. "Treating calculators as gospel". */
  claim: string;
  /** Trailing explanation. */
  explanation: string;
}

export interface NoteSections {
  title: string;
  /** "A2-BMR-TDEE" style stable id parsed from the **ID:** line. */
  schemaId?: string;
  quickTakeaway?: string;
  keyPoints: string[];
  deepDive?: string;
  evidence: EvidenceEntry[];
  practicalApplications?: string;
  commonMistakes: CommonMistake[];
  /** Free prose that links out via [[wikilinks]] — feeds the next-up logic. */
  relatedConcepts?: string;
  /** Anything that didn't match a known section, kept so we never lose content. */
  extraSections: { heading: string; body: string }[];
}

const KNOWN_HEADINGS: Record<string, keyof NoteSections | 'extra'> = {
  'quick takeaway': 'quickTakeaway',
  'key points': 'keyPoints',
  'deep dive': 'deepDive',
  'research evidence': 'evidence',
  'practical applications': 'practicalApplications',
  'common mistakes': 'commonMistakes',
  'related concepts': 'relatedConcepts',
  'update log': 'extra',
};

interface RawSection {
  heading: string;
  level: number;
  body: string;
}

function splitTopLevelSections(content: string): { title: string; schemaId?: string; sections: RawSection[] } {
  const lines = content.split('\n');

  let title = '';
  let schemaId: string | undefined;

  // Find leading title (### in our notes) before the first ## section.
  let cursor = 0;
  for (; cursor < lines.length; cursor++) {
    const line = lines[cursor];
    if (!title) {
      const titleMatch = line.match(/^#{1,3}\s+(.+?)\s*$/);
      if (titleMatch) {
        title = titleMatch[1].replace(/^[A-Z]{1,4}\d+\.\s*/, '').trim();
        if (!title) title = titleMatch[1].trim();
        continue;
      }
    }
    const idMatch = line.match(/^\*\*ID:\*\*\s+(.+)$/);
    if (idMatch) {
      schemaId = idMatch[1].trim();
      continue;
    }
    if (/^##\s+/.test(line)) break;
  }

  const sections: RawSection[] = [];
  let current: RawSection | null = null;
  for (; cursor < lines.length; cursor++) {
    const line = lines[cursor];
    const headingMatch = line.match(/^(#{2,3})\s+(.+?)\s*$/);
    if (headingMatch) {
      if (current) sections.push(current);
      current = {
        heading: headingMatch[2].trim(),
        level: headingMatch[1].length,
        body: '',
      };
      continue;
    }
    if (current) {
      current.body += line + '\n';
    }
  }
  if (current) sections.push(current);

  return { title, schemaId, sections };
}

function parseKeyPoints(body: string): string[] {
  return body
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => /^[-*]\s+/.test(l))
    .map((l) => l.replace(/^[-*]\s+/, '').trim())
    .filter(Boolean);
}

function parseCommonMistakes(body: string): CommonMistake[] {
  const out: CommonMistake[] = [];
  // Each mistake usually starts with a warning glyph then **bold claim** - explanation.
  const lines = body.split('\n').map((l) => l.trim()).filter(Boolean);
  for (const line of lines) {
    // Strip leading warning glyphs (⚠️, ❗, etc.) — they're presentational.
    const stripped = line.replace(/^[^\w*]+/, '');
    const match = stripped.match(/^\*\*(.+?)\*\*\s*[-—:]\s*(.+)$/);
    if (match) {
      out.push({ claim: match[1].trim(), explanation: match[2].trim() });
    }
  }
  return out;
}

const QUALITY_RE = /Evidence quality:\s*(High|Medium|Low)\b\s*(?:\(([^)]+)\))?/i;

function hashId(input: string): string {
  // FNV-1a 32-bit, deterministic and dependency-free.
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

function parseEvidence(body: string): EvidenceEntry[] {
  const entries: EvidenceEntry[] = [];
  // A citation block starts with **Author...(Year).** and runs until the next **Author or end.
  const blocks = body.split(/\n(?=\*\*[A-Z][^*]*\(\d{4}\)\.\*\*)/);
  for (const raw of blocks) {
    const block = raw.trim();
    if (!block.startsWith('**')) continue;

    const headerMatch = block.match(/^\*\*([^*]+?)\*\*\s*([\s\S]*)$/);
    if (!headerMatch) continue;

    const authorYear = headerMatch[1].trim();
    const rest = headerMatch[2];
    const lines = rest.split('\n').map((l) => l.trim());

    const citationLine = lines.find((l) => l && !l.startsWith('-')) ?? '';
    const keyFinding = lines.find((l) => /^- ?Key finding:/i.test(l))?.replace(/^- ?Key finding:\s*/i, '');
    const studyType = lines.find((l) => /^- ?Study type:/i.test(l))?.replace(/^- ?Study type:\s*/i, '');
    const qualityLine = lines.find((l) => /^- ?Evidence quality:/i.test(l)) ?? '';
    const qualityMatch = qualityLine.match(QUALITY_RE);

    const citation = `${authorYear}. ${citationLine}`.trim();
    entries.push({
      id: hashId(citation),
      citation,
      authorYear,
      keyFinding,
      studyType,
      quality: (qualityMatch?.[1] as EvidenceQuality) ?? 'Unknown',
      qualityNote: qualityMatch?.[2]?.trim(),
    });
  }
  return entries;
}

export function parseNoteSections(content: string): NoteSections {
  const { title, schemaId, sections } = splitTopLevelSections(content);

  const result: NoteSections = {
    title,
    schemaId,
    keyPoints: [],
    evidence: [],
    commonMistakes: [],
    extraSections: [],
  };

  for (const section of sections) {
    const key = KNOWN_HEADINGS[section.heading.toLowerCase()];
    const body = section.body.trim();
    switch (key) {
      case 'quickTakeaway':
        result.quickTakeaway = body;
        break;
      case 'keyPoints':
        result.keyPoints = parseKeyPoints(body);
        break;
      case 'deepDive':
        result.deepDive = body;
        break;
      case 'evidence':
        result.evidence = parseEvidence(body);
        break;
      case 'practicalApplications':
        result.practicalApplications = body;
        break;
      case 'commonMistakes':
        result.commonMistakes = parseCommonMistakes(body);
        break;
      case 'relatedConcepts':
        result.relatedConcepts = body;
        break;
      case 'extra':
        // Intentionally drop "Update Log" from the user-facing surface.
        break;
      default:
        result.extraSections.push({ heading: section.heading, body });
    }
  }

  return result;
}

/** Best-effort tl;dr suitable for hover popovers and graph node tooltips. */
export function summariseForPreview(sections: NoteSections, maxChars = 220): string {
  const source = sections.quickTakeaway || sections.keyPoints[0] || sections.deepDive || '';
  const flat = source.replace(/\s+/g, ' ').trim();
  if (flat.length <= maxChars) return flat;
  return flat.slice(0, maxChars - 1).replace(/[\s,.;:]+\S*$/, '') + '…';
}
