/**
 * Wikipedia-style hover popover for [[wikilinks]].
 *
 * Pedagogy note: most navigations to a linked note are unnecessary — the
 * learner just needs to remind themselves what the term means. Letting them
 * peek without context-switching keeps cognitive load on the *current* idea
 * (Sweller's CLT — minimise extraneous load).
 *
 * Lifecycle:
 *   1. Mouse enters wikilink with a 180ms delay (avoids accidental triggers).
 *   2. Fetch the target node JSON (cached).
 *   3. Parse with `parseNoteSections`, render the Quick Takeaway + 3 key points.
 *   4. Click "Open as panel" pushes onto the stack.
 */

import React, { useEffect, useRef, useState } from 'react';
import type { NodeData } from '../types';
import { parseNoteSections, summariseForPreview } from '../lib/noteSchema';
import { EvidencePill } from './EvidencePill';

interface Props {
  /** Coordinates relative to viewport for the popover anchor. */
  anchor: { x: number; y: number };
  fetchNode: (id: string) => Promise<NodeData | null>;
  targetId: string;
  onOpen: () => void;
  onClose: () => void;
}

export const NoteHoverCard: React.FC<Props> = ({ anchor, fetchNode, targetId, onOpen, onClose }) => {
  const [node, setNode] = useState<NodeData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    fetchNode(targetId)
      .then((n) => {
        if (cancelled) return;
        if (!n) setError('Linked note not found.');
        else setNode(n);
      })
      .catch(() => !cancelled && setError('Failed to load preview.'));
    return () => {
      cancelled = true;
    };
  }, [fetchNode, targetId]);

  const sections = node ? parseNoteSections(node.content) : null;

  // Flip the popover above the cursor if it would overflow the viewport.
  const placement = React.useMemo(() => {
    if (typeof window === 'undefined') return { left: anchor.x, top: anchor.y + 16 };
    const w = 360;
    const h = 240;
    const left = Math.min(window.innerWidth - w - 16, Math.max(16, anchor.x - 24));
    const flip = anchor.y + h + 24 > window.innerHeight;
    const top = flip ? Math.max(16, anchor.y - h - 12) : anchor.y + 16;
    return { left, top };
  }, [anchor.x, anchor.y]);

  return (
    <div
      ref={cardRef}
      role="dialog"
      onMouseLeave={onClose}
      className="fixed z-[200] w-[360px] rounded-2xl p-5"
      style={{
        ...placement,
        background: 'var(--paper-raised)',
        border: '1px solid var(--hairline)',
        boxShadow: '0 12px 40px -12px rgba(0,0,0,0.4)',
      }}
    >
      {error && (
        <p className="text-xs" style={{ color: '#E07B7B' }}>
          {error}
        </p>
      )}
      {!error && !node && (
        <div className="space-y-2 animate-pulse">
          <div className="h-3 w-3/4 rounded" style={{ background: 'var(--paper-elevated)' }} />
          <div className="h-3 w-full rounded" style={{ background: 'var(--paper-elevated)' }} />
          <div className="h-3 w-5/6 rounded" style={{ background: 'var(--paper-elevated)' }} />
        </div>
      )}
      {node && sections && (
        <>
          <header className="flex items-start justify-between gap-3 mb-2">
            <h4
              className="text-sm leading-tight"
              style={{
                color: 'var(--ink-strong)',
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
              }}
            >
              {node.title}
            </h4>
            <span
              className="font-mono text-[10px] uppercase tracking-widest shrink-0"
              style={{ color: 'var(--ink-faint)' }}
            >
              {node.series}
            </span>
          </header>

          <p
            className="text-sm leading-relaxed mb-3"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            {summariseForPreview(sections, 200)}
          </p>

          {sections.keyPoints.length > 0 && (
            <ul
              className="text-xs space-y-1 mb-3 list-disc pl-4"
              style={{ color: 'var(--ink-muted)' }}
            >
              {sections.keyPoints.slice(0, 3).map((kp, i) => (
                <li key={i} className="line-clamp-2">{kp}</li>
              ))}
            </ul>
          )}

          <footer
            className="flex items-center justify-between pt-2"
            style={{ borderTop: '1px solid var(--hairline)' }}
          >
            <div className="flex gap-2 items-center">
              {sections.evidence.slice(0, 1).map((e) => (
                <EvidencePill key={e.id} quality={e.quality} note={e.qualityNote} />
              ))}
              <span
                className="font-mono text-[10px] uppercase tracking-widest"
                style={{ color: 'var(--ink-faint)' }}
              >
                {sections.evidence.length} citations
              </span>
            </div>
            <button
              onClick={onOpen}
              className="font-mono text-[11px] uppercase tracking-widest hover:underline"
              style={{ color: 'var(--accent)' }}
            >
              Open as panel →
            </button>
          </footer>
        </>
      )}
    </div>
  );
};
