/**
 * Multi-column stacked reader (Andy Matuschak pattern).
 *
 * Two responsibilities:
 *
 * 1. Lay out a horizontally-scrolling stack of columns with a quiet,
 *    paper-coloured surface. The global graph lives elsewhere — the
 *    reader stays a reading surface.
 *
 * 2. Hydrate full note content on demand. The Library passes us a
 *    summary-level index (id, title, series, links, excerpt) which is
 *    enough for navigation/sidebar/sidekick lookups, but the body of a
 *    column needs the full note JSON. Without this hydration step the
 *    reader would only ever render the 220-char excerpt that lives on
 *    the index, which is exactly the bug that motivated this rewrite.
 *
 * Layout (z-order):
 *   z=0   Quiet paper background
 *   z=10  StackedReader columns
 *   z=200 NoteHoverCard popovers
 */

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { NodeData } from '../types';
import { useNoteStack } from '../lib/noteStack';
import { NoteReader } from './NoteReader';
import { NoteHoverCard } from './NoteHoverCard';
import { NoteSidekick } from './NoteSidekick';
import { recordVisit } from '../lib/recentlyViewed';
import { buildBacklinkIndex } from '../lib/backlinks';

interface Props {
  /**
   * Summary-level node index (typically from `searchNodes()` which only
   * carries the excerpt as `content`). Used for navigation, alias
   * resolution and the local graph; the reader hydrates full content via
   * `fetchNode` before rendering.
   */
  nodes: NodeData[];
  /** On-demand fetcher for a full node. Should resolve from the content bridge. */
  fetchNode: (id: string) => Promise<NodeData | null>;
  /** Optional initial stack if there's no `?stack=` in the URL. */
  initialStack?: string[];
  /** Optional externally-selected node (e.g. from sidebar click in Library). */
  externalOpenNodeId?: string | null;
}

interface HoverState {
  targetId: string;
  anchor: { x: number; y: number };
  fromNodeId: string;
}

export const StackedReader: React.FC<Props> = ({
  nodes,
  fetchNode,
  initialStack,
  externalOpenNodeId,
}) => {
  const { stack, pushAfter, open, closeFrom, closeAll } = useNoteStack();
  const containerRef = useRef<HTMLDivElement>(null);
  const [hover, setHover] = useState<HoverState | null>(null);
  const hoverTimer = useRef<number | null>(null);
  const didInitStack = useRef(false);
  const prevExternalOpenRef = useRef<string | null>(null);

  // Detail cache + in-flight set so React can render skeletons while we
  // wait for the full node JSON. Stored in state (a `Map` ref by way of a
  // version counter) so re-renders pick up new arrivals.
  const detailsRef = useRef<Map<string, NodeData>>(new Map());
  const pendingRef = useRef<Set<string>>(new Set());
  const [detailsVersion, setDetailsVersion] = useState(0);
  const bumpDetails = useCallback(() => setDetailsVersion((v) => v + 1), []);

  const ensureDetail = useCallback(
    async (id: string) => {
      if (!id) return;
      if (detailsRef.current.has(id)) return;
      if (pendingRef.current.has(id)) return;
      pendingRef.current.add(id);
      try {
        const full = await fetchNode(id);
        if (full) {
          detailsRef.current.set(id, full);
          bumpDetails();
        }
      } finally {
        pendingRef.current.delete(id);
      }
    },
    [fetchNode, bumpDetails]
  );

  // Apply initial stack once if URL is empty.
  useEffect(() => {
    if (didInitStack.current) return;
    if (stack.length === 0 && initialStack && initialStack.length > 0) {
      open(initialStack[0]);
      initialStack.slice(1).forEach((id, i) => pushAfter(initialStack[i], id));
    }
    didInitStack.current = true;
  }, [initialStack, open, pushAfter, stack.length]);

  // React to explicit external selection (sidebar clicks).
  useEffect(() => {
    if (!externalOpenNodeId) return;
    if (prevExternalOpenRef.current === externalOpenNodeId) return;
    if (!nodes.some((n) => n.id === externalOpenNodeId)) return;

    prevExternalOpenRef.current = externalOpenNodeId;
    open(externalOpenNodeId);
  }, [externalOpenNodeId, nodes, open]);

  // Auto-scroll rightmost column into view when stack grows.
  useEffect(() => {
    if (!containerRef.current) return;
    containerRef.current.scrollTo({
      left: containerRef.current.scrollWidth,
      behavior: 'smooth',
    });
  }, [stack.length]);

  // Hydrate every node currently in the stack.
  useEffect(() => {
    stack.forEach((id) => ensureDetail(id));
  }, [stack, ensureDetail]);

  // Record the focused (rightmost) note in the recently-viewed trail —
  // wait until the detail is hydrated so we record the real title.
  const lastRecordedRef = useRef<string | null>(null);
  useEffect(() => {
    const focusedId = stack[stack.length - 1];
    if (!focusedId || focusedId === lastRecordedRef.current) return;
    const detail = detailsRef.current.get(focusedId) || nodes.find((n) => n.id === focusedId);
    if (!detail) return;
    recordVisit({ id: detail.id, title: detail.title, series: detail.series });
    lastRecordedRef.current = focusedId;
  }, [stack, nodes, detailsVersion]);

  const backlinks = useMemo(() => buildBacklinkIndex(nodes), [nodes]);
  const focusedId = stack[stack.length - 1] ?? null;
  // Prefer hydrated detail for the focused node so sidekick stats reflect
  // the real (parsed) content instead of the excerpt.
  const focusedNode =
    (focusedId && detailsRef.current.get(focusedId)) ||
    (focusedId ? nodes.find((n) => n.id === focusedId) || null : null);

  const beginHover = (fromNodeId: string, targetId: string, anchor: { x: number; y: number }) => {
    if (hoverTimer.current) window.clearTimeout(hoverTimer.current);
    hoverTimer.current = window.setTimeout(() => {
      setHover({ targetId, anchor, fromNodeId });
    }, 180);
  };
  const endHover = () => {
    if (hoverTimer.current) window.clearTimeout(hoverTimer.current);
    hoverTimer.current = window.setTimeout(() => setHover(null), 160);
  };

  return (
    <div
      className="relative w-full h-full flex"
      style={{ background: 'var(--paper)' }}
    >
      <div
        ref={containerRef}
        className="relative z-10 flex-1 h-full overflow-x-auto overflow-y-hidden flex gap-6 px-6 py-6 scroll-smooth snap-x"
      >
        {stack.length === 0 && (
          <div
            className="m-auto max-w-md text-center"
            style={{ color: 'var(--ink-muted)' }}
          >
            <p
              className="text-base mb-2"
              style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}
            >
              Pick a note from the explorer to begin reading.
            </p>
            <p className="text-xs" style={{ color: 'var(--ink-faint)' }}>
              Tip: any [[wikilink]] inside a note opens the linked note in a
              new column to the right.
            </p>
          </div>
        )}
        {stack.map((nodeId, i) => {
          const summary = nodes.find((n) => n.id === nodeId);
          const detail = detailsRef.current.get(nodeId);
          // We render the column for any id that is in the stack, even if
          // the summary index doesn't have it yet (rare but possible if
          // someone deep-links a stale id).
          const node = detail || summary || null;
          const isFocused = i === stack.length - 1;
          const isLoading = !detail && (pendingRef.current.has(nodeId) || !summary);

          return (
            <div key={nodeId} className="snap-start h-full">
              {node ? (
                <NoteReader
                  node={node}
                  hydrated={Boolean(detail)}
                  index={nodes}
                  isFocused={isFocused}
                  onClose={i === 0 ? closeAll : () => closeFrom(nodeId)}
                  onWikilinkOpen={(fromId, targetId) => pushAfter(fromId, targetId)}
                  onWikilinkHover={(targetId, anchor) =>
                    beginHover(nodeId, targetId, anchor)
                  }
                  onWikilinkLeave={endHover}
                />
              ) : (
                <ReaderSkeleton id={nodeId} loading={isLoading} />
              )}
            </div>
          );
        })}
      </div>

      {focusedNode && detailsRef.current.has(focusedNode.id) && (
        <div
          className="hidden xl:block h-full overflow-y-auto py-6 pr-6 pl-2"
          style={{ background: 'var(--paper)' }}
        >
          <NoteSidekick
            focused={focusedNode}
            index={nodes}
            backlinks={backlinks}
            onOpenNode={(id) => pushAfter(focusedNode.id, id)}
          />
        </div>
      )}

      {hover && (
        <NoteHoverCard
          anchor={hover.anchor}
          fetchNode={fetchNode}
          targetId={hover.targetId}
          onOpen={() => {
            pushAfter(hover.fromNodeId, hover.targetId);
            setHover(null);
          }}
          onClose={endHover}
        />
      )}
    </div>
  );
};

const ReaderSkeleton: React.FC<{ id: string; loading: boolean }> = ({ id, loading }) => (
  <article
    className="relative flex flex-col h-full w-full max-w-[720px] shrink-0 rounded-2xl overflow-hidden"
    style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
  >
    <header
      className="px-8 pt-7 pb-5"
      style={{ borderBottom: '1px solid var(--hairline)' }}
    >
      <p
        className="font-mono text-[10px] tracking-widest uppercase mb-2"
        style={{ color: 'var(--ink-faint)' }}
      >
        {id}
      </p>
      <div
        className="h-7 rounded-md w-3/4 animate-pulse"
        style={{ background: 'var(--paper-elevated)' }}
      />
    </header>
    <div className="flex-1 overflow-y-auto px-8 py-8 space-y-4">
      {loading ? (
        [...Array(8)].map((_, i) => (
          <div
            key={i}
            className="h-3 rounded animate-pulse"
            style={{
              background: 'var(--paper-elevated)',
              width: `${[100, 92, 96, 78, 88, 100, 70, 84][i]}%`,
            }}
          />
        ))
      ) : (
        <p className="text-sm" style={{ color: 'var(--ink-faint)' }}>
          Note not found in the content bridge. Try refreshing or rebuilding
          the bridge with <code>npm run content:build</code>.
        </p>
      )}
    </div>
  </article>
);
