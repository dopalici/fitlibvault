/**
 * Generates fill-in-the-blank (cloze) cards from a parsed note's Key Points.
 *
 * Why cloze instead of MCQ:
 *   The generation effect (Slamecka & Graf, 1978) and active retrieval
 *   (Roediger & Karpicke, 2006) both show that producing the answer beats
 *   recognising it. Cloze cards force production while staying auto-buildable.
 *
 * Heuristic:
 *   - Prefer blanking out the most semantically loaded span:
 *     numeric ranges (e.g. "60–75%"), capitalised acronyms (BMR, NEAT),
 *     parenthesised expansions, then the longest noun-phrase candidate.
 *   - Skip points <40 chars: too thin to learn from.
 *   - Skip points whose only candidate is a stop-word or pronoun.
 *
 * Determinism:
 *   The same input always produces the same card id (FNV-1a hash), so cards
 *   survive content rebuilds without losing review history in the SRS store.
 */

import type { NoteSections } from './noteSchema';

export interface ClozeCard {
  id: string;
  nodeId: string;
  /** Text with the answer span replaced by ____ (use {{c1::...}} for richer rendering). */
  prompt: string;
  /** The exact answer span. */
  answer: string;
  /** Optional alternative acceptable answers (e.g. unit-stripped). */
  acceptableAnswers: string[];
  /** Plain-text preview for the deck UI. */
  context: string;
  /** Source: which Key Point index this came from, for debugging. */
  sourceIndex: number;
}

const STOPWORDS = new Set([
  'the', 'and', 'for', 'with', 'are', 'was', 'were', 'has', 'have', 'had',
  'this', 'that', 'these', 'those', 'their', 'your', 'our', 'its', 'his', 'her',
  'a', 'an', 'is', 'in', 'on', 'of', 'to', 'by', 'from', 'as', 'at', 'be',
  'or', 'but', 'not', 'than', 'then', 'so', 'if',
]);

function fnv1a(input: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i++) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(36);
}

interface Candidate {
  span: string;
  start: number;
  end: number;
  weight: number;
}

const NUMERIC_SPAN = /(\d{1,3}(?:[\.,]\d+)?[-–](?:\d{1,3}(?:[\.,]\d+)?))(\s*%)?/g;
const SOLO_PERCENT = /\b\d{1,3}(?:[\.,]\d+)?\s*%/g;
const ACRONYM = /\b[A-Z]{2,5}(?:\/[A-Z]{2,5})?\b/g;
const PARENTHETICAL = /\(([^)]{3,40})\)/g;
const QUANTITY_UNIT = /\b\d+(?:[\.,]\d+)?\s?(?:kcal|cal|g|mg|kg|hz|ms|reps?|sets?|min|sec|hours?|days?|weeks?)\b/gi;

function collectCandidates(point: string): Candidate[] {
  const cands: Candidate[] = [];

  const push = (re: RegExp, weight: number) => {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(point)) !== null) {
      const span = m[0];
      cands.push({ span, start: m.index, end: m.index + span.length, weight });
    }
  };

  push(NUMERIC_SPAN, 5);
  push(SOLO_PERCENT, 4);
  push(QUANTITY_UNIT, 4);
  push(ACRONYM, 3);
  push(PARENTHETICAL, 2);

  // Fallback: longest capitalised noun-phrase (e.g. "Mifflin-St Jeor equation").
  const NP = /\b([A-Z][a-zA-Z\-]+(?:\s+[A-Z][a-zA-Z\-]+){1,3})\b/g;
  let m: RegExpExecArray | null;
  while ((m = NP.exec(point)) !== null) {
    const span = m[1];
    if (STOPWORDS.has(span.toLowerCase())) continue;
    cands.push({ span, start: m.index, end: m.index + span.length, weight: 1 });
  }

  return cands;
}

function pickBest(cands: Candidate[]): Candidate | null {
  if (cands.length === 0) return null;
  return cands.reduce((best, c) =>
    c.weight > best.weight ||
    (c.weight === best.weight && c.span.length > best.span.length)
      ? c : best
  );
}

function blank(point: string, cand: Candidate): string {
  const before = point.slice(0, cand.start);
  const after = point.slice(cand.end);
  return `${before}____${after}`;
}

function acceptableVariants(answer: string): string[] {
  const out = new Set<string>([answer.trim()]);
  // Numeric: strip percent, hyphen variants, comma-vs-dot decimals.
  out.add(answer.replace(/\s+/g, ' ').trim());
  out.add(answer.replace(/–/g, '-'));
  out.add(answer.replace(/-/g, '–'));
  out.add(answer.replace('%', '').trim());
  out.add(answer.toLowerCase());
  return Array.from(out).filter(Boolean);
}

export function generateClozeCards(
  nodeId: string,
  sections: NoteSections,
): ClozeCard[] {
  const cards: ClozeCard[] = [];
  sections.keyPoints.forEach((point, i) => {
    if (point.length < 40) return;
    const cand = pickBest(collectCandidates(point));
    if (!cand) return;
    const id = fnv1a(`${nodeId}:${i}:${cand.span}:${point}`);
    cards.push({
      id,
      nodeId,
      prompt: blank(point, cand),
      answer: cand.span,
      acceptableAnswers: acceptableVariants(cand.span),
      context: point,
      sourceIndex: i,
    });
  });
  return cards;
}

/**
 * Lightweight grader. Lenient on whitespace, case, and trivial punctuation
 * because we want learners to feel the generation effect, not get punished
 * for typos. Numeric answers must match digits-and-units tolerantly.
 */
export function gradeAnswer(card: ClozeCard, attempt: string): boolean {
  const norm = (s: string) =>
    s.toLowerCase()
      .replace(/[–—]/g, '-')
      .replace(/[%,.]/g, '')
      .replace(/\s+/g, ' ')
      .trim();
  const target = card.acceptableAnswers.map(norm);
  const candidate = norm(attempt);
  if (!candidate) return false;
  return target.some((t) => t === candidate);
}
