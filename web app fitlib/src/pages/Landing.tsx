/**
 * Landing — the front cover of FitLib.
 *
 * Design intent (matching the rest of the rewrite):
 *   - Quiet typography over hype. Treat the page like the inside of a book
 *     jacket, not a SaaS marketing splash.
 *   - The hero number is real. We pull `totalNodes` and `totalCitations`
 *     straight from the content bridge so the front page can never lie
 *     about how much is in the library.
 *   - Two routes off this page — read or review. Sign-up isn't required;
 *     dev/admin builds skip it entirely.
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Brain,
  ScrollText,
  ShieldCheck,
  Sparkles,
  Network,
  Layers,
} from 'lucide-react';
import { loadLibraryStats, type LibraryStats } from '../lib/libraryStats';

export const Landing: React.FC = () => {
  const [stats, setStats] = useState<LibraryStats | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadLibraryStats().then((s) => !cancelled && setStats(s));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: 'var(--paper)' }}
    >
      {/* Brand bar — separate from the global TopBar (which doesn't render on /). */}
      <header className="px-6 py-5">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span
              className="w-7 h-7 rounded-md flex items-center justify-center font-black italic"
              style={{ background: 'var(--accent)', color: 'var(--paper)' }}
            >
              F
            </span>
            <span
              className="text-base font-semibold tracking-tight"
              style={{ color: 'var(--ink-strong)' }}
            >
              FitLib
            </span>
          </div>
          <nav className="flex items-center gap-1">
            <Link
              to="/about"
              className="px-3 py-1.5 rounded-md text-sm transition-colors hover:bg-[var(--paper-elevated)]"
              style={{ color: 'var(--ink-muted)' }}
            >
              Transparency
            </Link>
            <Link
              to="/dashboard"
              className="px-3 py-1.5 rounded-md text-sm transition-colors hover:bg-[var(--paper-elevated)]"
              style={{ color: 'var(--ink-muted)' }}
            >
              Dashboard
            </Link>
            <Link
              to="/library"
              className="ml-2 px-4 py-1.5 rounded-lg text-sm font-semibold transition-transform hover:translate-y-[-1px]"
              style={{ background: 'var(--accent)', color: 'var(--paper)' }}
            >
              Open the library
            </Link>
          </nav>
        </div>
      </header>

      {/* HERO */}
      <section className="px-6 pt-24 pb-20">
        <div className="max-w-3xl mx-auto text-center">
          <p
            className="font-mono text-[10px] uppercase tracking-[0.24em] mb-6 inline-flex items-center gap-2"
            style={{ color: 'var(--accent)' }}
          >
            <ShieldCheck className="w-3 h-3" /> Evidence-based fitness, indexed
          </p>
          <h1
            className="text-5xl md:text-7xl mb-7 leading-[1.02]"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
              letterSpacing: '-0.015em',
            }}
          >
            A reading library for the science of training.
          </h1>
          <p
            className="text-lg md:text-xl max-w-2xl mx-auto leading-relaxed mb-10"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            {stats
              ? `${stats.totalNodes.toLocaleString()} cross-linked notes, ${stats.totalCitations.toLocaleString()} cited papers, one disciplined schema. Read it like Wikipedia, recall it like Anki.`
              : 'Hundreds of cross-linked notes, every claim sourced. Read it like Wikipedia, recall it like Anki.'}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/library"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-transform hover:translate-y-[-1px]"
              style={{ background: 'var(--accent)', color: 'var(--paper)' }}
            >
              <ScrollText className="w-4 h-4" /> Start reading
            </Link>
            <Link
              to="/about"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold transition-colors hover:bg-[var(--paper-elevated)]"
              style={{
                color: 'var(--ink-strong)',
                border: '1px solid var(--hairline-strong)',
              }}
            >
              How it works <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* HERO METRICS */}
      <section className="px-6 pb-20">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3">
          <Metric label="Notes" value={stats?.totalNodes} />
          <Metric label="Citations" value={stats?.totalCitations} />
          <Metric label="Cross-links" value={stats?.totalLinks} />
          <Metric
            label="Recall cards"
            value={stats?.totalCards}
            hint={
              stats
                ? `${Math.round(stats.cardCoverage * 100)}% coverage`
                : undefined
            }
          />
        </div>
      </section>

      {/* WHY */}
      <section
        className="px-6 py-16"
        style={{
          borderTop: '1px solid var(--hairline)',
          borderBottom: '1px solid var(--hairline)',
          background: 'var(--paper-raised)',
        }}
      >
        <div className="max-w-5xl mx-auto">
          <p
            className="font-mono text-[10px] uppercase tracking-[0.2em] mb-2"
            style={{ color: 'var(--accent)' }}
          >
            How it reads
          </p>
          <h2
            className="text-3xl md:text-4xl mb-3"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
            }}
          >
            Built around four findings in cognitive science.
          </h2>
          <p
            className="leading-relaxed max-w-2xl mb-10"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            Reading fitness theory and forgetting it the next week is the
            normal experience. FitLib is a library shaped to fight that.
          </p>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Pillar
              icon={Layers}
              title="Stacked panels"
              body="Open a wikilink and the linked note slides in to the right. Hold context while expanding."
            />
            <Pillar
              icon={Brain}
              title="Active recall"
              body="Every focused note ends with a typed-answer block. Producing beats re-reading."
            />
            <Pillar
              icon={Sparkles}
              title="Spaced practice"
              body="FSRS schedules each cloze at the moment you're about to forget — without rote daily drills."
            />
            <Pillar
              icon={Network}
              title="Local graph"
              body="A 1-hop neighbourhood beside every note shows where the idea lives in the wider library."
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="px-6 py-20">
        <div className="max-w-3xl mx-auto text-center">
          <h2
            className="text-3xl md:text-4xl mb-5"
            style={{
              color: 'var(--ink-strong)',
              fontFamily: 'var(--font-serif)',
              fontWeight: 600,
            }}
          >
            Pick a note. Read it. Remember it.
          </h2>
          <p
            className="text-lg leading-relaxed mb-8 max-w-xl mx-auto"
            style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
          >
            No sign-up. The library is the product; the reader is the
            interface.
          </p>
          <Link
            to="/library"
            className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl text-sm font-semibold transition-transform hover:translate-y-[-1px]"
            style={{ background: 'var(--accent)', color: 'var(--paper)' }}
          >
            Open the library <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <footer
        className="px-6 py-8 text-center"
        style={{ borderTop: '1px solid var(--hairline)' }}
      >
        <p
          className="font-mono text-[11px]"
          style={{ color: 'var(--ink-faint)' }}
        >
          {stats?.generatedAt
            ? `Snapshot · ${new Date(stats.generatedAt).toLocaleString()}`
            : 'Static content bridge · public/content/index.json'}
        </p>
      </footer>
    </div>
  );
};

const Metric: React.FC<{ label: string; value?: number; hint?: string }> = ({
  label,
  value,
  hint,
}) => (
  <div
    className="rounded-2xl px-5 py-5 text-center"
    style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
  >
    <div
      className="text-3xl md:text-4xl font-semibold tabular-nums"
      style={{
        color: 'var(--ink-strong)',
        fontFamily: 'var(--font-serif)',
      }}
    >
      {value === undefined ? '—' : value.toLocaleString()}
    </div>
    <div
      className="font-mono text-[10px] uppercase tracking-widest mt-1"
      style={{ color: 'var(--ink-faint)' }}
    >
      {label}
      {hint && <span className="normal-case font-medium"> · {hint}</span>}
    </div>
  </div>
);

const Pillar: React.FC<{
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  title: string;
  body: string;
}> = ({ icon: Icon, title, body }) => (
  <div
    className="p-5 rounded-2xl"
    style={{ background: 'var(--paper)', border: '1px solid var(--hairline)' }}
  >
    <div
      className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
      style={{
        background: 'var(--accent-soft)',
        border: '1px solid var(--hairline)',
      }}
    >
      <Icon className="w-5 h-5" style={{ color: 'var(--accent)' }} />
    </div>
    <h3
      className="font-semibold text-base mb-1"
      style={{ color: 'var(--ink-strong)' }}
    >
      {title}
    </h3>
    <p
      className="text-sm leading-relaxed"
      style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
    >
      {body}
    </p>
  </div>
);
