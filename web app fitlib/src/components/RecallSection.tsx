/**
 * The "test yourself" block at the bottom of every focused note.
 *
 * Why this is non-negotiable:
 *   - Active recall (Roediger & Karpicke 2006) is the single best-replicated
 *     finding in learning research. Re-reading is *not* learning; producing is.
 *   - The generation effect (Slamecka & Graf 1978) means typing the answer
 *     beats just thinking it.
 *   - The reveal-then-rate flow drives FSRS scheduling so cards return at
 *     the right time (Cepeda et al. 2008 — spaced practice).
 *
 * UX rules:
 *   - "Show answer" button is small and quiet. "Check" is primary.
 *   - Default rating button is "Good", not "Easy" — desirable difficulty.
 *   - We never block the page; if the learner skips, fine. Just no false
 *     "I know this" pat-on-the-back without a retrieval attempt.
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Brain, Check, RotateCcw } from 'lucide-react';
import type { NoteSections } from '../lib/noteSchema';
import { generateClozeCards, gradeAnswer, type ClozeCard } from '../lib/clozeGen';
import { registerCards, recordReview, type ReviewRating } from '../lib/srs';
import { cn } from '../lib/utils';

interface Props {
  nodeId: string;
  sections: NoteSections;
}

export const RecallSection: React.FC<Props> = ({ nodeId, sections }) => {
  const cards = useMemo(() => generateClozeCards(nodeId, sections), [nodeId, sections]);
  const [registered, setRegistered] = useState(false);

  useEffect(() => {
    let cancelled = false;
    registerCards(cards).then(() => !cancelled && setRegistered(true)).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [cards]);

  if (cards.length === 0) return null;

  return (
    <section className="pt-6" style={{ borderTop: '1px solid var(--hairline)' }}>
      <div className="flex items-center justify-between mb-4">
        <h3
          className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em]"
          style={{ color: 'var(--ink-muted)' }}
        >
          <Brain className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
          Recall
        </h3>
        <span
          className="font-mono text-[10px] tracking-widest"
          style={{ color: 'var(--ink-faint)' }}
        >
          {cards.length} cards · active retrieval
        </span>
      </div>
      <div className="space-y-3">
        {cards.map((c) => (
          <ClozeRow key={c.id} card={c} disabled={!registered} />
        ))}
      </div>
      <p
        className="mt-4 text-xs leading-relaxed"
        style={{ color: 'var(--ink-faint)' }}
      >
        Cards repeat on a spaced schedule (FSRS). Producing the answer beats
        re-reading — even a wrong attempt before checking improves retention.
      </p>
    </section>
  );
};

const ClozeRow: React.FC<{ card: ClozeCard; disabled?: boolean }> = ({ card, disabled }) => {
  type Phase = 'attempt' | 'graded' | 'rated';
  const [phase, setPhase] = useState<Phase>('attempt');
  const [attempt, setAttempt] = useState('');
  const [correct, setCorrect] = useState<boolean | null>(null);

  const reset = () => {
    setPhase('attempt');
    setAttempt('');
    setCorrect(null);
  };

  const grade = () => {
    setCorrect(gradeAnswer(card, attempt));
    setPhase('graded');
  };

  const rate = async (rating: ReviewRating) => {
    await recordReview(card.id, rating);
    setPhase('rated');
  };

  return (
    <div
      className="rounded-xl px-4 py-3"
      style={{
        background: 'var(--paper-elevated)',
        border: '1px solid var(--hairline)',
      }}
    >
      <p
        className="text-base leading-relaxed"
        style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
      >
        {card.prompt.split('____').map((part, i, arr) => (
          <React.Fragment key={i}>
            {part}
            {i < arr.length - 1 &&
              (phase === 'attempt' ? (
                <input
                  value={attempt}
                  onChange={(e) => setAttempt(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && grade()}
                  disabled={disabled}
                  placeholder="…"
                  className="inline-block min-w-[6ch] mx-1 px-2 py-0.5 rounded text-sm focus:outline-none transition-colors"
                  style={{
                    background: 'var(--accent-soft)',
                    border: '1px solid color-mix(in oklab, var(--accent) 50%, transparent)',
                    color: 'var(--ink-strong)',
                    fontFamily: 'var(--font-sans)',
                  }}
                />
              ) : (
                <span
                  className="inline-block mx-1 px-2 py-0.5 rounded text-sm font-medium"
                  style={{
                    background: correct
                      ? 'color-mix(in oklab, #3CB371 18%, transparent)'
                      : 'color-mix(in oklab, #E07B7B 18%, transparent)',
                    border: `1px solid ${correct ? '#3CB371' : '#E07B7B'}`,
                    color: correct ? '#3CB371' : '#E07B7B',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  {card.answer}
                </span>
              ))}
          </React.Fragment>
        ))}
      </p>

      {phase === 'attempt' && (
        <div className="flex items-center justify-between mt-3">
          <button
            onClick={grade}
            disabled={disabled || attempt.length === 0}
            className={cn(
              'px-3 py-1.5 rounded-md text-xs font-semibold tracking-wider uppercase transition-colors',
              (disabled || attempt.length === 0) && 'opacity-40 cursor-not-allowed'
            )}
            style={{ background: 'var(--accent)', color: 'var(--paper)' }}
          >
            Check
          </button>
          <button
            onClick={() => {
              setAttempt('');
              grade();
            }}
            disabled={disabled}
            className="text-[11px] underline underline-offset-2"
            style={{ color: 'var(--ink-faint)' }}
          >
            Show answer
          </button>
        </div>
      )}

      {phase === 'graded' && (
        <div className="flex flex-wrap items-center gap-2 mt-3">
          <span
            className="text-[11px] font-semibold uppercase tracking-widest mr-1"
            style={{ color: correct ? '#3CB371' : '#E07B7B' }}
          >
            {correct ? 'Correct' : 'Not quite'}
          </span>
          <RatingButton onClick={() => rate('again')} tone="again">Again</RatingButton>
          <RatingButton onClick={() => rate('hard')} tone="hard">Hard</RatingButton>
          <RatingButton onClick={() => rate('good')} tone="good" emphasis>Good</RatingButton>
          <RatingButton onClick={() => rate('easy')} tone="easy">Easy</RatingButton>
        </div>
      )}

      {phase === 'rated' && (
        <div
          className="flex items-center gap-2 mt-3 text-[11px]"
          style={{ color: '#3CB371' }}
        >
          <Check className="w-3.5 h-3.5" />
          Scheduled.
          <button
            onClick={reset}
            className="ml-2 inline-flex items-center gap-1 underline underline-offset-2"
            style={{ color: 'var(--ink-faint)' }}
          >
            <RotateCcw className="w-3 h-3" /> Retry
          </button>
        </div>
      )}
    </div>
  );
};

const RatingButton: React.FC<{
  onClick: () => void;
  tone: 'again' | 'hard' | 'good' | 'easy';
  emphasis?: boolean;
  children: React.ReactNode;
}> = ({ onClick, tone, emphasis, children }) => {
  const colour =
    tone === 'again' ? '#E07B7B' :
    tone === 'hard' ? 'var(--warm)' :
    tone === 'good' ? 'var(--accent)' :
    'var(--ink-muted)';
  return (
    <button
      onClick={onClick}
      className="px-3 py-1 rounded-md text-[11px] font-semibold uppercase tracking-widest transition-colors"
      style={{
        border: `1px solid color-mix(in oklab, ${colour} 50%, transparent)`,
        color: colour,
        background: emphasis
          ? `color-mix(in oklab, ${colour} 12%, transparent)`
          : 'transparent',
      }}
    >
      {children}
    </button>
  );
};
