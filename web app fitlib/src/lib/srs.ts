/**
 * Spaced repetition scheduler backed by FSRS-4 (better than Anki's SM-2).
 *
 * Persistence is local-first via IndexedDB (Dexie) — zero backend, survives
 * refresh, syncs trivially later if you want it to.
 *
 * Why FSRS:
 *   - Optimises stability and retention from real review history rather than
 *     hand-tuned multipliers, so it adapts to each learner.
 *   - Empirically beats SM-2 in the open Anki community trials.
 *
 * Required deps (run once):
 *   npm i ts-fsrs dexie
 */

import Dexie, { type Table } from 'dexie';
import {
  createEmptyCard,
  fsrs,
  generatorParameters,
  Rating,
  State,
  type Card as FsrsCard,
  type ReviewLog,
} from 'ts-fsrs';
import type { ClozeCard } from './clozeGen';

export type ReviewRating = 'again' | 'hard' | 'good' | 'easy';

const RATING_MAP: Record<ReviewRating, Rating> = {
  again: Rating.Again,
  hard: Rating.Hard,
  good: Rating.Good,
  easy: Rating.Easy,
};

interface StoredCard {
  /** ClozeCard.id — stable across content rebuilds. */
  id: string;
  nodeId: string;
  fsrs: FsrsCard;
  /** Cached due timestamp (ms) for fast IndexedDB indexed queries. */
  due: number;
  introducedAt: number;
}

interface StoredReview {
  cardId: string;
  reviewedAt: number;
  rating: ReviewRating;
  log: ReviewLog;
}

class FitLibSRSDB extends Dexie {
  cards!: Table<StoredCard, string>;
  reviews!: Table<StoredReview, number>;

  constructor() {
    super('fitlib-srs');
    this.version(1).stores({
      cards: 'id, nodeId, due',
      reviews: '++autoId, cardId, reviewedAt',
    });
  }
}

const db = new FitLibSRSDB();

const scheduler = fsrs(
  generatorParameters({
    enable_fuzz: true,
    maximum_interval: 365,
    request_retention: 0.9, // target 90% recall — calibrated for desirable difficulty
  })
);

function fsrsCardFromStored(stored: StoredCard): FsrsCard {
  return {
    ...stored.fsrs,
    due: new Date(stored.fsrs.due),
    last_review: stored.fsrs.last_review ? new Date(stored.fsrs.last_review) : undefined,
  };
}

/**
 * Ensure every cloze card has an entry in the SRS store. Newly added cards
 * land due now so they're picked up on the next session.
 */
export async function registerCards(cards: ClozeCard[]): Promise<void> {
  if (cards.length === 0) return;
  const existing = await db.cards.bulkGet(cards.map((c) => c.id));
  const now = Date.now();
  const inserts: StoredCard[] = [];
  cards.forEach((card, i) => {
    if (existing[i]) return;
    const fresh = createEmptyCard(new Date(now));
    inserts.push({
      id: card.id,
      nodeId: card.nodeId,
      fsrs: fresh,
      due: fresh.due.getTime(),
      introducedAt: now,
    });
  });
  if (inserts.length > 0) await db.cards.bulkAdd(inserts);
}

export interface DueCard {
  storedId: string;
  nodeId: string;
  state: State;
  due: Date;
}

export async function getDueCards(nodeId?: string, limit = 20): Promise<DueCard[]> {
  const now = Date.now();
  let query = db.cards.where('due').belowOrEqual(now);
  let rows = await query.toArray();
  if (nodeId) rows = rows.filter((r) => r.nodeId === nodeId);
  rows.sort((a, b) => a.due - b.due);
  return rows.slice(0, limit).map((r) => ({
    storedId: r.id,
    nodeId: r.nodeId,
    state: r.fsrs.state,
    due: new Date(r.fsrs.due),
  }));
}

export async function recordReview(
  cardId: string,
  rating: ReviewRating,
  reviewedAt: Date = new Date()
): Promise<void> {
  const stored = await db.cards.get(cardId);
  if (!stored) return;
  const fsrsCard = fsrsCardFromStored(stored);
  const recordLog = scheduler.repeat(fsrsCard, reviewedAt);
  const next = recordLog[RATING_MAP[rating]];

  await db.transaction('rw', db.cards, db.reviews, async () => {
    await db.cards.put({
      ...stored,
      fsrs: next.card,
      due: next.card.due.getTime(),
    });
    await db.reviews.add({
      cardId,
      reviewedAt: reviewedAt.getTime(),
      rating,
      log: next.log,
    });
  });
}

export interface LearnerStats {
  totalCards: number;
  dueToday: number;
  reviewedLast7Days: number;
  retention7d: number;
  matureCards: number;
}

export async function getLearnerStats(): Promise<LearnerStats> {
  const now = Date.now();
  const weekAgo = now - 7 * 24 * 60 * 60 * 1000;

  const [totalCards, dueRows, recentReviews] = await Promise.all([
    db.cards.count(),
    db.cards.where('due').belowOrEqual(now).toArray(),
    db.reviews.where('reviewedAt').above(weekAgo).toArray(),
  ]);

  const recentNonAgain = recentReviews.filter((r) => r.rating !== 'again').length;
  const retention7d = recentReviews.length === 0
    ? 0
    : recentNonAgain / recentReviews.length;

  const matureCards = await db.cards
    .filter((c) => c.fsrs.scheduled_days >= 21 && c.fsrs.state === State.Review)
    .count();

  return {
    totalCards,
    dueToday: dueRows.length,
    reviewedLast7Days: recentReviews.length,
    retention7d,
    matureCards,
  };
}

/**
 * Interleaving recommender. Given a freshly-completed node, return the next
 * node id from a *different* series (Rohrer & Taylor, 2007 — interleaving
 * beats blocking when concepts are confusable). Falls back to same series
 * if no off-series candidate exists.
 */
export function recommendNextNode<T extends { id: string; series: string; links?: string[] }>(
  current: T,
  candidates: T[],
): T | undefined {
  const linkSet = new Set(current.links ?? []);
  const offSeries = candidates.filter(
    (c) => c.id !== current.id && c.series !== current.series && linkSet.has(c.id)
  );
  if (offSeries.length > 0) return offSeries[0];
  const sameSeries = candidates.filter(
    (c) => c.id !== current.id && linkSet.has(c.id)
  );
  return sameSeries[0];
}
