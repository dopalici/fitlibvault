/**
 * Section-aware note reader.
 *
 * Renders the structured FitLib schema (Quick Takeaway, Key Points, Deep Dive,
 * Evidence, Practical Applications, Common Mistakes) using a calm, paper-on-ink
 * surface — no neon, no frosted glass. The body uses a serif type face so long
 * passages feel like reading a book; chrome stays sans-serif so it doesn't
 * compete with the prose.
 *
 * If the parser ends up with nothing recognised in any of the structured
 * sections (rare, but happens for legacy notes that predate the schema), we
 * fall back to rendering the raw markdown so the column never sits blank —
 * the reader's job is to render content, full stop.
 */

import React, { useEffect, useMemo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { ChevronRight, X, Beaker, ListChecks, Zap, Wrench, AlertTriangle, Bookmark } from 'lucide-react';
import type { NodeData } from '../types';
import { parseNoteSections, summariseForPreview } from '../lib/noteSchema';
import { buildWikilinkResolver, convertWikilinksToMarkdown } from '../lib/wikilinks';
import { EvidencePill } from './EvidencePill';
import { cn } from '../lib/utils';
import { RecallSection } from './RecallSection';
import { isFavorite, subscribeFavorites, toggleFavorite } from '../lib/favorites';

interface Props {
  node: NodeData;
  /** Other nodes used for wiki-link resolution + hover previews. */
  index: NodeData[];
  onWikilinkOpen: (fromNodeId: string, targetId: string) => void;
  onWikilinkHover?: (targetId: string, anchor: { x: number; y: number }) => void;
  onWikilinkLeave?: () => void;
  onClose?: () => void;
  className?: string;
  /** When true, this column owns keyboard focus and full feature set. */
  isFocused?: boolean;
  /**
   * True when `node.content` is the full markdown body (from the content
   * bridge / API), rather than the index-level excerpt. The reader uses
   * this to decide whether to run the structured-section parser at all
   * and whether the raw-markdown fallback should kick in.
   */
  hydrated?: boolean;
}

export const NoteReader: React.FC<Props> = ({
  node,
  index,
  onWikilinkOpen,
  onWikilinkHover,
  onWikilinkLeave,
  onClose,
  className,
  isFocused,
  hydrated = true,
}) => {
  // Only run the structured-schema parser on hydrated bodies. The index-level
  // excerpt is a 220-char preview and would always look like an off-schema
  // fragment, triggering the raw-markdown fallback with garbled output.
  const sections = useMemo(
    () => (hydrated ? parseNoteSections(node.content) : null),
    [node.content, hydrated]
  );
  const resolver = useMemo(() => buildWikilinkResolver(index), [index]);
  const [favorited, setFavorited] = useState<boolean>(() => isFavorite(node.id));

  useEffect(() => {
    setFavorited(isFavorite(node.id));
    return subscribeFavorites(() => setFavorited(isFavorite(node.id)));
  }, [node.id]);

  const handleToggleFavorite = () => {
    const next = toggleFavorite({ id: node.id, title: node.title, series: node.series });
    setFavorited(next);
  };

  const renderProse = (markdown: string) => {
    const md = convertWikilinksToMarkdown(markdown, resolver);
    return (
      <ReactMarkdown
        components={{
          a: ({ href, children }) => {
            if (href?.startsWith('fitlib://node/')) {
              const targetId = decodeURIComponent(href.replace('fitlib://node/', ''));
              return (
                <button
                  type="button"
                  onClick={() => onWikilinkOpen(node.id, targetId)}
                  onMouseEnter={(e) => onWikilinkHover?.(targetId, { x: e.clientX, y: e.clientY })}
                  onMouseLeave={onWikilinkLeave}
                  className="text-accent underline decoration-[var(--accent-soft)] underline-offset-4 hover:decoration-accent transition-colors"
                  style={{ color: 'var(--accent)' }}
                >
                  {children}
                </button>
              );
            }
            return (
              <a
                href={href}
                target="_blank"
                rel="noreferrer"
                className="underline underline-offset-4 transition-colors"
                style={{ color: 'var(--accent)' }}
              >
                {children}
              </a>
            );
          },
        }}
      >
        {md}
      </ReactMarkdown>
    );
  };

  const hasStructuredContent =
    sections != null &&
    (Boolean(sections.quickTakeaway) ||
      sections.keyPoints.length > 0 ||
      Boolean(sections.deepDive) ||
      sections.evidence.length > 0 ||
      Boolean(sections.practicalApplications) ||
      sections.commonMistakes.length > 0 ||
      Boolean(sections.relatedConcepts));

  return (
    <article
      className={cn(
        'relative flex flex-col h-full w-full max-w-[720px] shrink-0 rounded-2xl transition-shadow',
        'border bg-paper-raised',
        isFocused
          ? 'shadow-[0_8px_30px_-10px_rgba(0,0,0,0.4)]'
          : 'opacity-[0.97]',
        className
      )}
      style={{ borderColor: 'var(--hairline)' }}
    >
      <header
        className="flex items-start justify-between gap-3 px-8 pt-7 pb-5"
        style={{ borderBottom: '1px solid var(--hairline)' }}
      >
        <div className="min-w-0">
          <p
            className="font-mono text-[10px] tracking-widest uppercase mb-1.5"
            style={{ color: 'var(--ink-faint)' }}
          >
            Series {node.series} · {node.id}
          </p>
          <h1
            className="text-2xl font-semibold leading-tight truncate"
            style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
          >
            {node.title}
          </h1>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={handleToggleFavorite}
            aria-label={favorited ? 'Remove from favourites' : 'Add to favourites'}
            title={favorited ? 'Saved to favourites' : 'Save to favourites'}
            className="p-2 rounded-lg transition-colors hover:bg-[var(--paper-elevated)]"
            style={{ color: favorited ? 'var(--warm)' : 'var(--ink-faint)' }}
          >
            <Bookmark className={cn('w-4 h-4', favorited && 'fill-current')} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              aria-label="Close column"
              className="p-2 rounded-lg transition-colors hover:bg-[var(--paper-elevated)]"
              style={{ color: 'var(--ink-faint)' }}
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-8 py-8 space-y-9 scroll-smooth">
        {!hydrated && (
          <section
            className="rounded-2xl px-6 py-5 flex items-center gap-3"
            style={{
              background: 'var(--paper-elevated)',
              border: '1px dashed var(--hairline-strong)',
            }}
          >
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ background: 'var(--accent)' }}
            />
            <p className="text-xs" style={{ color: 'var(--ink-muted)' }}>
              Loading the full note from the content bridge…
            </p>
          </section>
        )}

        {hydrated && !hasStructuredContent && (
          // Graceful fallback: when the schema parser finds nothing, the
          // raw markdown is the next-best signal of what the file holds.
          // Rendering it keeps the reader honest — we never silently swallow
          // content just because it's off-schema.
          <section>
            <SectionHeader label="Note" />
            <div className="prose-body">
              {renderProse(node.content || '_No content available._')}
            </div>
          </section>
        )}

        {sections && (<>
        {sections.quickTakeaway && (
          <section
            className="rounded-2xl px-6 py-5"
            style={{
              background: 'var(--accent-soft)',
              border: '1px solid var(--hairline)',
            }}
          >
            <p
              className="font-mono text-[10px] tracking-widest uppercase mb-2"
              style={{ color: 'var(--accent)' }}
            >
              tl;dr
            </p>
            <p
              className="text-[1.0625rem] leading-relaxed"
              style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
            >
              {summariseForPreview(sections, 600)}
            </p>
          </section>
        )}

        {sections.keyPoints.length > 0 && (
          <section>
            <SectionHeader icon={ListChecks} label="Key points" />
            <ol className="space-y-3 list-none">
              {sections.keyPoints.map((kp, i) => (
                <li
                  key={i}
                  className="flex gap-3.5 text-[1rem] leading-relaxed"
                  style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
                >
                  <span
                    className="font-mono text-xs shrink-0 mt-1.5 tabular-nums"
                    style={{ color: 'var(--ink-faint)' }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <span>{kp}</span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {sections.deepDive && (
          <section>
            <SectionHeader icon={Beaker} label="Deep dive" />
            <div className="prose-body">{renderProse(sections.deepDive)}</div>
          </section>
        )}

        {sections.evidence.length > 0 && (
          <section>
            <SectionHeader icon={Beaker} label="Evidence" trailing={`${sections.evidence.length} cited`} />
            <ul className="space-y-3">
              {sections.evidence.map((e) => (
                <li
                  key={e.id}
                  className="rounded-xl p-4"
                  style={{
                    background: 'var(--paper-elevated)',
                    border: '1px solid var(--hairline)',
                  }}
                >
                  <div className="flex items-start justify-between gap-3 mb-1.5">
                    <p
                      className="text-sm font-semibold"
                      style={{ color: 'var(--ink-strong)' }}
                    >
                      {e.authorYear}
                    </p>
                    <EvidencePill quality={e.quality} note={e.qualityNote} />
                  </div>
                  {e.keyFinding && (
                    <p
                      className="text-sm leading-relaxed mb-1"
                      style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
                    >
                      {e.keyFinding}
                    </p>
                  )}
                  {e.studyType && (
                    <p className="text-xs" style={{ color: 'var(--ink-faint)' }}>
                      {e.studyType}
                    </p>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}

        {sections.practicalApplications && (
          <section>
            <SectionHeader icon={Wrench} label="Practical applications" />
            <div
              className="rounded-xl pl-6 pr-4 py-4 prose-body"
              style={{
                borderLeft: '2px solid color-mix(in oklab, var(--accent) 60%, transparent)',
                background: 'var(--accent-soft)',
              }}
            >
              {renderProse(sections.practicalApplications)}
            </div>
          </section>
        )}

        {sections.commonMistakes.length > 0 && (
          <section>
            <SectionHeader icon={AlertTriangle} label="Common mistakes" />
            <ul className="space-y-2">
              {sections.commonMistakes.map((m, i) => (
                <li
                  key={i}
                  className="rounded-xl px-4 py-3"
                  style={{
                    border: '1px solid color-mix(in oklab, var(--warm) 30%, transparent)',
                    background: 'color-mix(in oklab, var(--warm) 8%, transparent)',
                  }}
                >
                  <p
                    className="text-sm font-semibold mb-1"
                    style={{ color: 'var(--ink-strong)' }}
                  >
                    {m.claim}
                  </p>
                  <p
                    className="text-sm leading-relaxed"
                    style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
                  >
                    {m.explanation}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        )}

        {isFocused && <RecallSection nodeId={node.id} sections={sections} />}

        {sections.relatedConcepts && (
          <section>
            <SectionHeader icon={Zap} label="Related" />
            <div className="prose-body">{renderProse(sections.relatedConcepts)}</div>
            <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2">
              {node.links?.map((linkId) => {
                const linked = index.find((n) => n.id === linkId);
                if (!linked) return null;
                return (
                  <button
                    key={linkId}
                    onClick={() => onWikilinkOpen(node.id, linkId)}
                    className="flex items-center justify-between text-left rounded-lg px-3 py-2.5 transition-colors group hover:bg-[var(--paper-elevated)]"
                    style={{ border: '1px solid var(--hairline)' }}
                  >
                    <span
                      className="text-sm truncate"
                      style={{ color: 'var(--ink)' }}
                    >
                      {linked.title}
                    </span>
                    <ChevronRight
                      className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-all"
                      style={{ color: 'var(--ink-faint)' }}
                    />
                  </button>
                );
              })}
            </div>
          </section>
        )}
        </>)}
      </div>
    </article>
  );
};

interface SectionHeaderProps {
  icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  trailing?: string;
}

const SectionHeader: React.FC<SectionHeaderProps> = ({ icon: Icon, label, trailing }) => (
  <div className="flex items-center justify-between mb-4">
    <h3
      className="flex items-center gap-2 text-xs font-semibold tracking-wide"
      style={{ color: 'var(--ink-muted)' }}
    >
      {Icon && <Icon className="w-3.5 h-3.5" style={{ color: 'var(--ink-faint)' }} />}
      <span className="uppercase tracking-[0.14em]">{label}</span>
    </h3>
    {trailing && (
      <span
        className="text-[11px] tabular-nums tracking-wide"
        style={{ color: 'var(--ink-faint)' }}
      >
        {trailing}
      </span>
    )}
  </div>
);
