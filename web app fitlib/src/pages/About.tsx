/**
 * Transparency — what's actually inside the library you're reading.
 *
 * Reskinned to match the reader's paper-on-ink theme. Every number on this
 * page reads live from the static content bridge that ships with the build:
 *   - public/content/index.json   (node summaries + metadata)
 *   - public/content/cards.json   (cloze deck index)
 *   - public/content/nodes/*.json (full notes; sampled for evidence grading)
 *
 * Each section is also a navigation hook: clicking a series tile drops you
 * into the Library filtered by that series so you can audit the actual
 * notes behind every number.
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  ArrowRight,
  Database,
  Cpu,
  RefreshCcw,
  Network,
  AlertTriangle,
  Brain,
  Layers,
  Library,
  Sparkles,
  CheckCircle2,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { loadLibraryStats, seriesLabel, seriesTone, type LibraryStats } from '../lib/libraryStats';

export const About: React.FC = () => {
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    loadLibraryStats()
      .then((s) => !cancelled && setStats(s))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const generatedAt = stats?.generatedAt ? new Date(stats.generatedAt) : null;
  const evidenceTotal =
    (stats?.evidenceQuality.High ?? 0) +
    (stats?.evidenceQuality.Medium ?? 0) +
    (stats?.evidenceQuality.Low ?? 0) +
    (stats?.evidenceQuality.Unknown ?? 0);

  const heroMetrics = useMemo(() => {
    if (!stats) {
      return [
        { label: 'Library nodes', value: '—' },
        { label: 'Citations indexed', value: '—' },
        { label: 'Recall cards', value: '—' },
        { label: 'Card coverage', value: '—' },
      ];
    }
    return [
      { label: 'Library nodes', value: stats.totalNodes.toLocaleString() },
      { label: 'Citations indexed', value: stats.totalCitations.toLocaleString() },
      { label: 'Recall cards', value: stats.totalCards.toLocaleString() },
      {
        label: 'Card coverage',
        value: `${Math.round(stats.cardCoverage * 100)}%`,
      },
    ];
  }, [stats]);

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: 'var(--paper)' }}
    >
      {/* HERO */}
      <section className="px-6 pt-16 pb-12">
        <div className="max-w-4xl mx-auto text-center">
          <span
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full font-mono text-[10px] font-semibold uppercase tracking-[0.2em] mb-6"
            style={{
              background: 'var(--accent-soft)',
              color: 'var(--accent)',
              border: '1px solid var(--hairline)',
            }}
          >
            <ShieldCheck className="w-3 h-3" /> Live transparency snapshot
          </span>
          <h1
            className="text-5xl md:text-6xl mb-6 leading-[1.05]"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
              letterSpacing: '-0.01em',
            }}
          >
            Show your work.
          </h1>
          <p
            className="text-base md:text-lg mb-10 max-w-2xl mx-auto leading-relaxed"
            style={{ color: 'var(--ink-muted)' }}
          >
            Every number on this page reads live from the static content
            bridge that ships with this build. Click a series to jump into
            the actual notes behind that count.
          </p>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 max-w-3xl mx-auto">
            {heroMetrics.map((m) => (
              <div
                key={m.label}
                className="p-4 rounded-2xl"
                style={{
                  background: 'var(--paper-raised)',
                  border: '1px solid var(--hairline)',
                }}
              >
                <div
                  className="text-3xl font-semibold tabular-nums mb-1"
                  style={{ color: 'var(--ink-strong)' }}
                >
                  {loading && stats === null ? '…' : m.value}
                </div>
                <div
                  className="font-mono text-[10px] uppercase tracking-widest"
                  style={{ color: 'var(--ink-faint)' }}
                >
                  {m.label}
                </div>
              </div>
            ))}
          </div>

          {generatedAt && (
            <p
              className="font-mono text-[11px] mt-8"
              style={{ color: 'var(--ink-faint)' }}
            >
              Snapshot generated {generatedAt.toLocaleString()}
            </p>
          )}
        </div>
      </section>

      {/* SERIES */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-end justify-between mb-8 flex-wrap gap-4">
            <div>
              <p
                className="font-mono text-[10px] uppercase tracking-[0.2em] mb-2"
                style={{ color: 'var(--accent)' }}
              >
                What's inside
              </p>
              <h2
                className="text-3xl"
                style={{
                  color: 'var(--ink-strong)',
                  fontFamily: 'var(--font-serif)',
                  fontWeight: 600,
                }}
              >
                Library by series
              </h2>
              <p
                className="text-sm max-w-xl mt-2"
                style={{ color: 'var(--ink-muted)' }}
              >
                Every series corresponds to a folder in the source vault.
                Credibility is the average evidence-grade weight of every
                note in that series.
              </p>
            </div>
            <Link
              to="/library"
              className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] hover:underline"
              style={{ color: 'var(--ink-muted)' }}
            >
              <Library className="w-3.5 h-3.5" /> Open the library
            </Link>
          </div>

          {loading && !stats && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 animate-pulse">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div
                  key={i}
                  className="h-28 rounded-2xl"
                  style={{ background: 'var(--paper-raised)' }}
                />
              ))}
            </div>
          )}

          {stats && stats.series.length > 0 && (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {stats.series.map((s) => {
                const tone = seriesTone(s.series);
                const sharePct = stats.totalNodes === 0 ? 0 : (s.total / stats.totalNodes) * 100;
                return (
                  <Link
                    key={s.series}
                    to={`/library?series=${encodeURIComponent(s.series)}`}
                    className="group relative p-5 rounded-2xl transition-colors hover:bg-[var(--paper-elevated)]"
                    style={{
                      background: 'var(--paper-raised)',
                      border: '1px solid var(--hairline)',
                    }}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className={cn('w-1.5 h-1.5 rounded-full', tone.dot)} />
                        <span
                          className="font-mono text-[10px] uppercase tracking-[0.18em]"
                          style={{ color: 'var(--ink-faint)' }}
                        >
                          Series {s.series}
                        </span>
                      </div>
                      <ArrowRight
                        className="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
                        style={{ color: 'var(--ink-faint)' }}
                      />
                    </div>
                    <h3
                      className="text-lg mb-1"
                      style={{
                        color: 'var(--ink-strong)',
                        fontFamily: 'var(--font-serif)',
                        fontWeight: 600,
                      }}
                    >
                      {seriesLabel(s.series)}
                    </h3>
                    <div className="flex items-center justify-between font-mono text-[11px] mb-3">
                      <span style={{ color: 'var(--ink-muted)' }}>
                        {s.total} nodes · {s.totalLinks} cross-links
                      </span>
                      <span className={tone.text}>
                        {(s.averageCredibility * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div
                      className="h-1.5 rounded-full overflow-hidden"
                      style={{ background: 'var(--paper-elevated)' }}
                    >
                      <div
                        className={cn('h-full', tone.dot)}
                        style={{ width: `${sharePct}%` }}
                      />
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>

      {/* EVIDENCE QUALITY */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-12 items-start">
          <div>
            <p
              className="font-mono text-[10px] uppercase tracking-[0.2em] mb-2"
              style={{ color: 'var(--accent)' }}
            >
              How we grade evidence
            </p>
            <h2
              className="text-3xl mb-4"
              style={{
                color: 'var(--ink-strong)',
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
              }}
            >
              Evidence quality breakdown
            </h2>
            <p
              className="leading-relaxed mb-6"
              style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
            >
              Each citation in a note is tagged{' '}
              <strong style={{ color: '#3CB371' }}>High</strong>,{' '}
              <strong style={{ color: 'var(--warm)' }}>Medium</strong>,{' '}
              <strong style={{ color: '#E07B7B' }}>Low</strong>, or{' '}
              <strong style={{ color: 'var(--ink-muted)' }}>Unknown</strong>{' '}
              following the GRADE framework. The chart on the right is
              computed by parsing a stratified sample of node JSONs in this
              build — same parser the reader uses, so what you see is what
              you read.
            </p>
            <div className="grid grid-cols-2 gap-3 max-w-md">
              {(['High', 'Medium', 'Low', 'Unknown'] as const).map((q) => {
                const count = stats?.evidenceQuality[q] ?? 0;
                const colour =
                  q === 'High'
                    ? '#3CB371'
                    : q === 'Medium'
                    ? 'var(--warm)'
                    : q === 'Low'
                    ? '#E07B7B'
                    : 'var(--ink-muted)';
                return (
                  <div
                    key={q}
                    className="p-4 rounded-xl"
                    style={{
                      background: 'var(--paper-raised)',
                      border: '1px solid var(--hairline)',
                    }}
                  >
                    <div
                      className="text-2xl font-semibold tabular-nums"
                      style={{ color: colour }}
                    >
                      {count}
                    </div>
                    <div
                      className="font-mono text-[10px] uppercase tracking-widest"
                      style={{ color: 'var(--ink-faint)' }}
                    >
                      {q} evidence
                    </div>
                  </div>
                );
              })}
            </div>
            <p
              className="font-mono text-[10px] mt-4"
              style={{ color: 'var(--ink-faint)' }}
            >
              Sampled from {Math.min(64, stats?.totalNodes ?? 0)} of{' '}
              {stats?.totalNodes ?? 0} nodes · {evidenceTotal} citations
              parsed
            </p>
          </div>

          <div
            className="p-6 rounded-3xl"
            style={{
              background: 'var(--paper-raised)',
              border: '1px solid var(--hairline)',
            }}
          >
            <h3
              className="text-base mb-5"
              style={{
                color: 'var(--ink-strong)',
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
              }}
            >
              Distribution
            </h3>
            <EvidenceBars stats={stats} total={evidenceTotal} />
            <p
              className="text-xs leading-relaxed mt-6"
              style={{ color: 'var(--ink-muted)' }}
            >
              The Library reader pins these grades as colour-coded pills
              next to each citation, so the source quality stays visible
              while you read.
            </p>
          </div>
        </div>
      </section>

      {/* LEARNING METHOD */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          <p
            className="font-mono text-[10px] uppercase tracking-[0.2em] mb-2"
            style={{ color: 'var(--accent)' }}
          >
            How learning works in FitLib
          </p>
          <h2
            className="text-3xl mb-3"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
            }}
          >
            Reader, recall, repeat.
          </h2>
          <p
            className="max-w-3xl leading-relaxed mb-10"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            The reader is built around four well-replicated findings in
            cognitive science. The Dashboard's "Today's recall queue" is a
            direct readout of how this loop is performing on your local FSRS
            deck.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              {
                icon: Layers,
                title: 'Stacked panels',
                body: 'Each [[wikilink]] opens to the right of the current note, so you can hold context while expanding.',
                cite: 'Andy Matuschak — Working with the Garage Door Up',
              },
              {
                icon: Brain,
                title: 'Active recall',
                body: 'Every focused note ends with a recall block where you produce the answer before checking.',
                cite: 'Roediger & Karpicke (2006); Slamecka & Graf (1978)',
              },
              {
                icon: RefreshCcw,
                title: 'Spaced practice',
                body: 'FSRS-4 schedules each cloze just before you forget it, prioritising desirable difficulty.',
                cite: 'Cepeda et al. (2008); Bjork & Bjork (1992)',
              },
              {
                icon: Sparkles,
                title: 'Interleaving',
                body: 'After a session, the reader recommends the next note from a different series when a link exists.',
                cite: 'Rohrer & Taylor (2007)',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="p-5 rounded-2xl transition-colors"
                style={{
                  background: 'var(--paper-raised)',
                  border: '1px solid var(--hairline)',
                }}
              >
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
                  style={{
                    background: 'var(--accent-soft)',
                    border: '1px solid var(--hairline)',
                  }}
                >
                  <item.icon
                    className="w-5 h-5"
                    style={{ color: 'var(--accent)' }}
                  />
                </div>
                <h3
                  className="font-semibold text-base mb-1"
                  style={{ color: 'var(--ink-strong)' }}
                >
                  {item.title}
                </h3>
                <p
                  className="text-sm leading-relaxed mb-3"
                  style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
                >
                  {item.body}
                </p>
                <p
                  className="text-[11px] italic leading-snug"
                  style={{ color: 'var(--ink-faint)' }}
                >
                  {item.cite}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PIPELINE */}
      <section className="py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p
              className="font-mono text-[10px] uppercase tracking-[0.2em] mb-2"
              style={{ color: 'var(--accent)' }}
            >
              Pipeline
            </p>
            <h2
              className="text-3xl mb-3"
              style={{
                color: 'var(--ink-strong)',
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
              }}
            >
              Automation quality gates
            </h2>
            <p
              className="text-sm max-w-2xl mx-auto"
              style={{ color: 'var(--ink-muted)' }}
            >
              Every note travels through these stages before it lands in
              the reader. Gate counts come from the same content bridge
              metadata you can inspect under{' '}
              <code>public/content/index.json</code>.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 relative">
            <div
              className="hidden md:block absolute top-7 left-0 w-full h-px z-0"
              style={{ background: 'var(--hairline)' }}
            />
            {[
              {
                icon: Database,
                label: 'Ingestion',
                value: stats ? `${stats.totalNodes} nodes` : '—',
              },
              {
                icon: Network,
                label: 'Cross-links',
                value: stats ? `${stats.totalLinks}` : '—',
              },
              {
                icon: Cpu,
                label: 'Recall cards',
                value: stats ? `${stats.totalCards}` : '—',
              },
              {
                icon: AlertTriangle,
                label: 'Broken links',
                value:
                  stats?.brokenWikilinks !== undefined
                    ? `${stats.brokenWikilinks}`
                    : '—',
                tone: 'amber' as const,
              },
              {
                icon: CheckCircle2,
                label: 'Coverage',
                value: stats ? `${Math.round(stats.cardCoverage * 100)}%` : '—',
              },
            ].map((node, i) => {
              const tone = node.tone === 'amber' ? 'var(--warm)' : 'var(--ink-muted)';
              return (
                <div
                  key={i}
                  className="relative z-10 flex flex-col items-center text-center gap-3"
                >
                  <div
                    className="w-14 h-14 rounded-full flex items-center justify-center"
                    style={{
                      background: 'var(--paper)',
                      border: `2px solid ${tone}`,
                    }}
                  >
                    <node.icon className="w-6 h-6" style={{ color: tone }} />
                  </div>
                  <div className="space-y-1">
                    <div
                      className="text-xl font-semibold tabular-nums"
                      style={{ color: 'var(--ink-strong)' }}
                    >
                      {node.value}
                    </div>
                    <div
                      className="font-mono text-[10px] uppercase tracking-widest"
                      style={{ color: 'var(--ink-faint)' }}
                    >
                      {node.label}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {stats?.brokenWikilinks !== undefined && stats.brokenWikilinks > 0 && (
            <p
              className="mt-8 text-sm text-center"
              style={{ color: 'var(--warm)' }}
            >
              <AlertTriangle className="inline w-3.5 h-3.5 mr-1 -mt-0.5" />
              {stats.brokenWikilinks} wikilinks in the source vault didn't
              resolve to a published node. They render as plain text in the
              reader so nothing silently misroutes.
            </p>
          )}
        </div>
      </section>

      {/* CTA */}
      <section
        className="py-16 px-6"
        style={{
          background: 'var(--paper-raised)',
          borderTop: '1px solid var(--hairline)',
          borderBottom: '1px solid var(--hairline)',
        }}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h2
            className="text-3xl md:text-4xl mb-6"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
            }}
          >
            Trust, but verify.
          </h2>
          <p
            className="text-base mb-10 max-w-xl mx-auto leading-relaxed"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            Every claim in the reader is rendered from a markdown file you
            can inspect; every citation has a quality grade and a visible
            source.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/library"
              className="px-6 py-3 rounded-xl text-sm font-semibold inline-flex items-center justify-center gap-2 transition-transform hover:translate-y-[-1px]"
              style={{ background: 'var(--accent)', color: 'var(--paper)' }}
            >
              Open the library <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/dashboard"
              className="px-6 py-3 rounded-xl text-sm font-semibold inline-flex items-center justify-center gap-2 transition-colors hover:bg-[var(--paper-elevated)]"
              style={{
                background: 'transparent',
                color: 'var(--ink-strong)',
                border: '1px solid var(--hairline-strong)',
              }}
            >
              See your dashboard
            </Link>
          </div>
        </div>
      </section>

      <footer className="py-10 text-center" style={{ borderTop: '1px solid var(--hairline)' }}>
        <p className="font-mono text-[11px]" style={{ color: 'var(--ink-faint)' }}>
          Content bridge: <code>public/content/index.json</code> ·{' '}
          <code>public/content/cards.json</code>
          {generatedAt && <> · {generatedAt.toLocaleString()}</>}
        </p>
      </footer>
    </div>
  );
};

const EvidenceBars: React.FC<{ stats: LibraryStats | null; total: number }> = ({
  stats,
  total,
}) => {
  const rows: { label: string; key: 'High' | 'Medium' | 'Low' | 'Unknown'; bar: string }[] = [
    { label: 'High', key: 'High', bar: '#3CB371' },
    { label: 'Medium', key: 'Medium', bar: 'var(--warm)' },
    { label: 'Low', key: 'Low', bar: '#E07B7B' },
    { label: 'Unknown', key: 'Unknown', bar: 'var(--ink-faint)' },
  ];
  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const value = stats?.evidenceQuality[row.key] ?? 0;
        const pct = total === 0 ? 0 : (value / total) * 100;
        return (
          <div key={row.key} className="space-y-1.5">
            <div className="flex items-end justify-between text-xs">
              <span className="font-medium" style={{ color: 'var(--ink-strong)' }}>
                {row.label}
              </span>
              <span className="font-mono tabular-nums" style={{ color: 'var(--ink-muted)' }}>
                {value}{' '}
                <span style={{ color: 'var(--ink-faint)' }}>
                  ({pct.toFixed(0)}%)
                </span>
              </span>
            </div>
            <div
              className="h-2 rounded-full overflow-hidden"
              style={{ background: 'var(--paper-elevated)' }}
            >
              <div
                className="h-full transition-all duration-700"
                style={{ width: `${pct}%`, background: row.bar }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
