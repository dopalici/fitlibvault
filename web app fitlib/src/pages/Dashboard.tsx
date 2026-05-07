/**
 * Dashboard — the learner's mission control.
 *
 * Reskinned to match the Library's paper-on-ink aesthetic. Layout still
 * follows the same evidence-based pedagogy:
 *
 *   1. Active recall over passive scrolling. The hero CTA deep-links into
 *      the stacked reader pre-loaded with every node that has FSRS cards
 *      due now.
 *   2. Real metrics, never mock. FSRS retention, due counts, mature cards
 *      come from the IndexedDB-backed FSRS store; library progress reads
 *      from the content bridge JSON; recently-viewed comes from
 *      localStorage written by the StackedReader.
 *   3. Single click to resume. Every card is a `?stack=` link.
 *   4. Admin parity. Demo mode is bypassed for `npm run dev` and any build
 *      with `VITE_DEV_ADMIN=true`.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BookOpen,
  ChevronRight,
  Search,
  Bookmark,
  LogIn,
  LogOut,
  Loader2,
  Brain,
  Shield,
  RefreshCw,
  Trash2,
  Sparkles,
  Target,
  Zap,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { DataImporter } from '../components/DataImporter';
import { auth } from '../lib/firebase';
import {
  GoogleAuthProvider,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  type User,
} from 'firebase/auth';
import { isAdminUser } from '../lib/admin';
import { env } from '../lib/env';
import { getDueCards, getLearnerStats, type LearnerStats } from '../lib/srs';
import {
  getRecentlyViewed,
  relativeTimeFrom,
  clearRecentlyViewed,
  type RecentNodeEntry,
} from '../lib/recentlyViewed';
import {
  getFavorites,
  subscribeFavorites,
  type FavoriteEntry,
} from '../lib/favorites';
import { loadLibraryStats, seriesLabel, seriesTone, type LibraryStats } from '../lib/libraryStats';

interface DueByNode {
  nodeId: string;
  due: number;
}

export const Dashboard: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [stats, setStats] = useState<LibraryStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [learnerStats, setLearnerStats] = useState<LearnerStats | null>(null);
  const [dueByNode, setDueByNode] = useState<DueByNode[]>([]);
  const [recent, setRecent] = useState<RecentNodeEntry[]>(() => getRecentlyViewed(6));
  const [favorites, setFavorites] = useState<FavoriteEntry[]>(() => getFavorites());

  useEffect(() => onAuthStateChanged(auth, (u) => setUser(u)), []);

  const refreshLearner = useCallback(async () => {
    const [s, due] = await Promise.all([getLearnerStats(), getDueCards(undefined, 200)]);
    setLearnerStats(s);
    const grouped = new Map<string, number>();
    due.forEach((card) => grouped.set(card.nodeId, (grouped.get(card.nodeId) || 0) + 1));
    setDueByNode(
      Array.from(grouped.entries())
        .map(([nodeId, dueCount]) => ({ nodeId, due: dueCount }))
        .sort((a, b) => b.due - a.due)
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    setStatsLoading(true);
    loadLibraryStats()
      .then((s) => !cancelled && setStats(s))
      .finally(() => !cancelled && setStatsLoading(false));
    refreshLearner().catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [refreshLearner]);

  useEffect(() => subscribeFavorites(() => setFavorites(getFavorites())), []);

  useEffect(() => {
    const refresh = () => setRecent(getRecentlyViewed(6));
    window.addEventListener('focus', refresh);
    return () => window.removeEventListener('focus', refresh);
  }, []);

  const handleLogin = async () => {
    if (isLoggingIn) return;
    setIsLoggingIn(true);
    const provider = new GoogleAuthProvider();
    try {
      await signInWithPopup(auth, provider);
    } catch (err) {
      if (err instanceof Error && !err.message.includes('auth/cancelled-popup-request')) {
        console.error('Login failed', err);
      }
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => signOut(auth);

  const showAdminTools = isAdminUser(user);
  const dueTotal = learnerStats?.dueToday ?? 0;
  const matureCards = learnerStats?.matureCards ?? 0;
  const retention = learnerStats?.retention7d ?? 0;
  const reviewedLast7 = learnerStats?.reviewedLast7Days ?? 0;
  const totalCardsScheduled = learnerStats?.totalCards ?? 0;

  const reviewSessionHref = useMemo(() => {
    if (dueByNode.length === 0) return '/library';
    const stack = dueByNode.slice(0, 6).map((d) => d.nodeId).join(',');
    return `/library?stack=${encodeURIComponent(stack)}`;
  }, [dueByNode]);

  const greetingName = user?.displayName?.split(' ')[0] || (env.devAdmin ? 'Admin' : 'Reader');

  return (
    <div
      className="flex-1 min-h-0 overflow-y-auto"
      style={{ background: 'var(--paper)' }}
    >
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-10">
        <Header
          user={user}
          isLoggingIn={isLoggingIn}
          onLogin={handleLogin}
          onLogout={handleLogout}
          showAdminBadge={showAdminTools}
          greetingName={greetingName}
          generatedAt={stats?.generatedAt}
          statsLoading={statsLoading}
        />

        <ReviewSessionCTA
          dueTotal={dueTotal}
          matureCards={matureCards}
          retention={retention}
          reviewedLast7={reviewedLast7}
          reviewSessionHref={reviewSessionHref}
          totalCards={totalCardsScheduled}
        />

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-3 space-y-8">
            <ContinueReading
              recent={recent}
              onClear={() => {
                clearRecentlyViewed();
                setRecent([]);
              }}
            />
            <FavoritesPanel favorites={favorites} />
          </div>

          <div className="lg:col-span-6 space-y-8">
            <RecallStats stats={learnerStats} onRefresh={refreshLearner} />
            <DueByNode dueByNode={dueByNode} />
            <CurriculumMastery stats={stats} loading={statsLoading} />
          </div>

          <div className="lg:col-span-3 space-y-8">
            <QuickSearch />
            <LearningMethod />
            {showAdminTools && (
              <AdminPanel
                statsGeneratedAt={stats?.generatedAt}
                onRefreshStats={async () => {
                  setStatsLoading(true);
                  const fresh = await loadLibraryStats(true);
                  setStats(fresh);
                  setStatsLoading(false);
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface HeaderProps {
  user: User | null;
  isLoggingIn: boolean;
  onLogin: () => void;
  onLogout: () => void;
  showAdminBadge: boolean;
  greetingName: string;
  generatedAt?: string;
  statsLoading: boolean;
}

const Header: React.FC<HeaderProps> = ({
  user,
  isLoggingIn,
  onLogin,
  onLogout,
  showAdminBadge,
  greetingName,
  generatedAt,
  statsLoading,
}) => {
  const lastBuilt = generatedAt ? new Date(generatedAt) : null;
  return (
    <header className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-8">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <h1
            className="text-3xl md:text-4xl font-semibold tracking-tight"
            style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
          >
            Welcome back, {greetingName}
          </h1>
          {showAdminBadge && (
            <span
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-mono text-[10px] font-semibold uppercase tracking-widest"
              style={{
                background: 'var(--accent-soft)',
                color: 'var(--accent)',
                border: '1px solid var(--hairline)',
              }}
            >
              <Shield className="w-3 h-3" /> Admin
            </span>
          )}
        </div>
        <p style={{ color: 'var(--ink-muted)' }}>
          Evidence-based learning, scheduled by your real review history.
        </p>
        {lastBuilt && (
          <p
            className="font-mono text-[11px] mt-1"
            style={{ color: 'var(--ink-faint)' }}
          >
            Library snapshot · {lastBuilt.toLocaleString()}
            {statsLoading && ' · refreshing…'}
          </p>
        )}
      </div>
      <div>
        {user ? (
          <button
            onClick={onLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors hover:bg-[var(--paper-elevated)]"
            style={{
              background: 'var(--paper-raised)',
              color: 'var(--ink-muted)',
              border: '1px solid var(--hairline)',
            }}
          >
            <LogOut className="w-4 h-4" /> Sign out
          </button>
        ) : (
          <button
            onClick={onLogin}
            disabled={isLoggingIn}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-colors',
              isLoggingIn && 'opacity-60 cursor-not-allowed'
            )}
            style={{
              background: 'var(--accent)',
              color: 'var(--paper)',
            }}
          >
            {isLoggingIn ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {isLoggingIn ? 'Connecting…' : 'Login with Google'}
          </button>
        )}
      </div>
    </header>
  );
};

interface ReviewCTAProps {
  dueTotal: number;
  matureCards: number;
  retention: number;
  reviewedLast7: number;
  totalCards: number;
  reviewSessionHref: string;
}

const ReviewSessionCTA: React.FC<ReviewCTAProps> = ({
  dueTotal,
  matureCards,
  retention,
  reviewedLast7,
  totalCards,
  reviewSessionHref,
}) => {
  const retentionPct = Math.round(retention * 100);
  const hasReviewed = totalCards > 0;
  return (
    <section
      className="rounded-3xl px-7 py-8 md:px-10 md:py-10 grid md:grid-cols-3 gap-8 items-center"
      style={{
        background: 'var(--paper-raised)',
        border: '1px solid var(--hairline)',
      }}
    >
      <div className="md:col-span-2">
        <p
          className="font-mono text-[10px] uppercase tracking-[0.2em] mb-3 inline-flex items-center gap-2"
          style={{ color: 'var(--accent)' }}
        >
          <Brain className="w-3.5 h-3.5" /> Today's recall queue
        </p>
        <h2
          className="text-3xl md:text-4xl leading-[1.15] mb-4"
          style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
        >
          {dueTotal === 0 && hasReviewed && 'All caught up — try a fresh note.'}
          {dueTotal === 0 && !hasReviewed && 'Open any note to start building your deck.'}
          {dueTotal > 0 && (
            <>
              <span style={{ color: 'var(--accent)' }}>{dueTotal}</span>{' '}
              {dueTotal === 1 ? 'card is' : 'cards are'} due now.
            </>
          )}
        </h2>
        <p
          className="text-base leading-relaxed max-w-2xl"
          style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
        >
          FSRS schedules each cloze when you're about to forget it — that's
          spaced practice with desirable difficulty (Cepeda et al. 2008,
          Bjork &amp; Bjork 1992). Producing the answer beats re-reading.
        </p>
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <Link
            to={reviewSessionHref}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold transition-transform hover:translate-y-[-1px]"
            style={{
              background: dueTotal > 0 ? 'var(--accent)' : 'var(--paper-elevated)',
              color: dueTotal > 0 ? 'var(--paper)' : 'var(--ink-strong)',
            }}
          >
            <Zap className="w-4 h-4" />
            {dueTotal > 0 ? 'Start review session' : 'Open the library'}
          </Link>
          <Link
            to="/about"
            className="font-mono text-[11px] uppercase tracking-[0.2em] hover:underline underline-offset-4"
            style={{ color: 'var(--ink-muted)' }}
          >
            How learning works →
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <Stat label="Cards" value={totalCards} />
        <Stat label="Mature" value={matureCards} hint=">21d" />
        <Stat
          label="Retention"
          value={hasReviewed ? `${retentionPct}%` : '—'}
          accent={
            retentionPct >= 85
              ? 'emerald'
              : retentionPct >= 70
              ? 'warm'
              : 'rose'
          }
        />
        <Stat label="Reviewed · 7d" value={reviewedLast7} />
      </div>
    </section>
  );
};

const Stat: React.FC<{
  label: string;
  value: React.ReactNode;
  hint?: string;
  accent?: 'emerald' | 'warm' | 'rose';
}> = ({ label, value, hint, accent }) => {
  const accentColor =
    accent === 'emerald'
      ? '#3CB371'
      : accent === 'warm'
      ? 'var(--warm)'
      : accent === 'rose'
      ? '#E07B7B'
      : 'var(--ink-strong)';
  return (
    <div
      className="rounded-xl px-4 py-3"
      style={{ background: 'var(--paper-elevated)', border: '1px solid var(--hairline)' }}
    >
      <div
        className="text-2xl font-semibold tabular-nums"
        style={{ color: accentColor }}
      >
        {value}
      </div>
      <div
        className="font-mono text-[10px] uppercase tracking-widest mt-0.5"
        style={{ color: 'var(--ink-faint)' }}
      >
        {label} {hint && <span className="normal-case">· {hint}</span>}
      </div>
    </div>
  );
};

const ContinueReading: React.FC<{ recent: RecentNodeEntry[]; onClear: () => void }> = ({
  recent,
  onClear,
}) => (
  <section>
    <div className="flex items-center justify-between mb-4">
      <h2
        className="text-base font-semibold flex items-center gap-2"
        style={{ color: 'var(--ink-strong)' }}
      >
        <BookOpen className="w-4 h-4" style={{ color: 'var(--ink-faint)' }} />
        Continue reading
      </h2>
      {recent.length > 0 && (
        <button
          onClick={onClear}
          className="font-mono text-[10px] uppercase tracking-widest inline-flex items-center gap-1 hover:underline"
          style={{ color: 'var(--ink-faint)' }}
        >
          <Trash2 className="w-3 h-3" /> Clear
        </button>
      )}
    </div>
    {recent.length === 0 ? (
      <EmptyHint
        cta="Browse the library"
        href="/library"
        message="Once you open notes in the reader, your trail shows up here so you can pick up exactly where you left off."
      />
    ) : (
      <div className="space-y-2.5">
        {recent.map((entry) => {
          const tone = seriesTone(entry.series);
          return (
            <Link
              key={entry.id}
              to={`/library?stack=${encodeURIComponent(entry.id)}`}
              className="block p-3.5 rounded-xl transition-colors hover:bg-[var(--paper-elevated)] group"
              style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span
                  className={cn('px-2 py-0.5 rounded font-mono text-[10px] font-semibold tracking-wider', tone.text, tone.bg)}
                >
                  Series {entry.series}
                </span>
                <span className="font-mono text-[10px]" style={{ color: 'var(--ink-faint)' }}>
                  {relativeTimeFrom(entry.viewedAt)}
                </span>
              </div>
              <h3
                className="font-medium text-sm leading-snug line-clamp-2 transition-colors"
                style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
              >
                {entry.title}
              </h3>
              <p className="text-[10px] mt-1.5" style={{ color: 'var(--ink-faint)' }}>
                {entry.views} {entry.views === 1 ? 'visit' : 'visits'}
              </p>
            </Link>
          );
        })}
      </div>
    )}
  </section>
);

const FavoritesPanel: React.FC<{ favorites: FavoriteEntry[] }> = ({ favorites }) => (
  <section>
    <div className="flex items-center justify-between mb-4">
      <h2
        className="text-base font-semibold flex items-center gap-2"
        style={{ color: 'var(--ink-strong)' }}
      >
        <Bookmark className="w-4 h-4" style={{ color: 'var(--warm)' }} />
        Saved notes
      </h2>
      <span
        className="font-mono text-[10px] uppercase tracking-widest"
        style={{ color: 'var(--ink-faint)' }}
      >
        {favorites.length}
      </span>
    </div>
    {favorites.length === 0 ? (
      <EmptyHint
        cta="Open a note"
        href="/library"
        message="Hit the bookmark icon on any note to keep a shortlist of go-to references."
      />
    ) : (
      <div className="space-y-1.5">
        {favorites.slice(0, 8).map((f) => {
          const tone = seriesTone(f.series);
          return (
            <Link
              key={f.id}
              to={`/library?stack=${encodeURIComponent(f.id)}`}
              className="flex items-center justify-between p-2.5 rounded-lg transition-colors hover:bg-[var(--paper-elevated)] group"
            >
              <div className="flex items-center gap-2 min-w-0">
                <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', tone.dot)} />
                <span
                  className="text-sm truncate"
                  style={{ color: 'var(--ink)' }}
                >
                  {f.title}
                </span>
              </div>
              <ChevronRight
                className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform"
                style={{ color: 'var(--ink-faint)' }}
              />
            </Link>
          );
        })}
      </div>
    )}
  </section>
);

const RecallStats: React.FC<{ stats: LearnerStats | null; onRefresh: () => Promise<void> }> = ({
  stats,
  onRefresh,
}) => {
  const totalReviewed = stats?.reviewedLast7Days ?? 0;
  const retention = stats?.retention7d ?? 0;
  const retentionPct = Math.round(retention * 100);
  const target = 90;
  return (
    <section className="grid grid-cols-1 md:grid-cols-3 gap-3">
      <BigStat label="Reviews · 7 days" value={totalReviewed} />
      <BigStat label="Cards mature" hint=">21d intervals" value={stats?.matureCards ?? 0} />
      <BigStat
        label="7-day retention"
        value={totalReviewed === 0 ? '—' : `${retentionPct}%`}
        hint={`target ${target}%`}
        action={
          <button
            onClick={() => onRefresh()}
            className="font-mono text-[10px] uppercase tracking-widest hover:underline inline-flex items-center gap-1"
            style={{ color: 'var(--ink-muted)' }}
          >
            <RefreshCw className="w-3 h-3" /> Refresh
          </button>
        }
      />
    </section>
  );
};

const BigStat: React.FC<{
  label: string;
  value: React.ReactNode;
  hint?: string;
  action?: React.ReactNode;
}> = ({ label, value, hint, action }) => (
  <div
    className="rounded-2xl px-5 py-5"
    style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
  >
    <div className="flex items-center justify-between mb-2">
      <p
        className="font-mono text-[10px] uppercase tracking-widest"
        style={{ color: 'var(--ink-faint)' }}
      >
        {label}
      </p>
      {action}
    </div>
    <div
      className="text-3xl md:text-4xl font-semibold tabular-nums"
      style={{ color: 'var(--ink-strong)' }}
    >
      {value}
    </div>
    {hint && (
      <p
        className="font-mono text-[10px] uppercase tracking-widest mt-1"
        style={{ color: 'var(--ink-faint)' }}
      >
        {hint}
      </p>
    )}
  </div>
);

const DueByNode: React.FC<{ dueByNode: DueByNode[] }> = ({ dueByNode }) => {
  if (dueByNode.length === 0) return null;
  return (
    <section
      className="p-6 rounded-2xl"
      style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
    >
      <h3
        className="text-lg font-semibold mb-4 flex items-center gap-2"
        style={{ color: 'var(--ink-strong)' }}
      >
        <Target className="w-4 h-4" style={{ color: 'var(--accent)' }} /> Notes due for recall
      </h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {dueByNode.slice(0, 6).map((entry) => (
          <Link
            key={entry.nodeId}
            to={`/library?stack=${encodeURIComponent(entry.nodeId)}`}
            className="flex items-center justify-between rounded-lg px-4 py-3 transition-colors hover:bg-[var(--paper-elevated)] group"
            style={{ border: '1px solid var(--hairline)' }}
          >
            <div className="min-w-0">
              <p
                className="text-sm font-semibold truncate"
                style={{ color: 'var(--ink-strong)' }}
              >
                {entry.nodeId}
              </p>
              <p
                className="font-mono text-[10px] uppercase tracking-widest"
                style={{ color: 'var(--ink-faint)' }}
              >
                {entry.due} card{entry.due === 1 ? '' : 's'} due
              </p>
            </div>
            <ChevronRight
              className="w-4 h-4 group-hover:translate-x-0.5 transition-transform"
              style={{ color: 'var(--ink-faint)' }}
            />
          </Link>
        ))}
      </div>
    </section>
  );
};

const CurriculumMastery: React.FC<{ stats: LibraryStats | null; loading: boolean }> = ({
  stats,
  loading,
}) => (
  <section
    className="p-6 md:p-8 rounded-2xl"
    style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
  >
    <div className="flex items-center justify-between mb-6">
      <h2
        className="text-xl font-semibold"
        style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
      >
        Curriculum mastery
      </h2>
      {stats && (
        <span
          className="font-mono text-[10px] uppercase tracking-widest"
          style={{ color: 'var(--ink-faint)' }}
        >
          {stats.totalNodes} nodes · {stats.totalLinks} links
        </span>
      )}
    </div>
    {loading && !stats && (
      <div className="space-y-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="h-3 rounded-full"
            style={{ background: 'var(--paper-elevated)' }}
          />
        ))}
      </div>
    )}
    {stats && stats.series.length > 0 && (
      <div className="space-y-5">
        {stats.series.map((s) => {
          const tone = seriesTone(s.series);
          const pct = stats.totalNodes === 0 ? 0 : (s.total / stats.totalNodes) * 100;
          return (
            <Link
              key={s.series}
              to={`/library?series=${encodeURIComponent(s.series)}`}
              className="block group"
            >
              <div className="flex justify-between items-end mb-1.5">
                <div className="flex items-center gap-2">
                  <span className={cn('w-1.5 h-1.5 rounded-full', tone.dot)} />
                  <span
                    className="font-medium text-sm transition-colors"
                    style={{ color: 'var(--ink-strong)' }}
                  >
                    {seriesLabel(s.series)}
                  </span>
                </div>
                <span
                  className="font-mono text-[11px] tabular-nums"
                  style={{ color: 'var(--ink-muted)' }}
                >
                  <span className={tone.text}>{s.total}</span> / {stats.totalNodes} nodes ·{' '}
                  {(s.averageCredibility * 100).toFixed(0)}% credibility
                </span>
              </div>
              <div
                className="h-1.5 rounded-full overflow-hidden"
                style={{ background: 'var(--paper-elevated)' }}
              >
                <div
                  className={cn('h-full transition-all', tone.dot)}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </Link>
          );
        })}
      </div>
    )}
    {stats && stats.series.length === 0 && (
      <p className="text-sm" style={{ color: 'var(--ink-faint)' }}>
        No series data yet — run <code>npm run content:build</code> to generate the bridge.
      </p>
    )}
  </section>
);

const QuickSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  return (
    <section
      className="p-5 rounded-2xl"
      style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
    >
      <h3
        className="font-semibold mb-3 text-sm flex items-center gap-2"
        style={{ color: 'var(--ink-strong)' }}
      >
        <Search className="w-3.5 h-3.5" style={{ color: 'var(--ink-faint)' }} />
        Quick search
      </h3>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          const trimmed = query.trim();
          if (!trimmed) return;
          window.location.href = `/library?search=${encodeURIComponent(trimmed)}`;
        }}
        className="relative"
      >
        <Search
          className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5"
          style={{ color: 'var(--ink-faint)' }}
        />
        <input
          type="text"
          placeholder="Search the library…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-lg py-2 pl-10 pr-4 text-sm outline-none transition-colors"
          style={{
            background: 'var(--paper)',
            color: 'var(--ink)',
            border: '1px solid var(--hairline)',
          }}
        />
      </form>
    </section>
  );
};

const LearningMethod: React.FC = () => (
  <section
    className="p-5 rounded-2xl"
    style={{ background: 'var(--accent-soft)', border: '1px solid var(--hairline)' }}
  >
    <h3
      className="font-semibold flex items-center gap-2 text-sm mb-2"
      style={{ color: 'var(--ink-strong)' }}
    >
      <Sparkles className="w-3.5 h-3.5" style={{ color: 'var(--accent)' }} />
      How this works
    </h3>
    <p
      className="text-sm leading-relaxed mb-4"
      style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
    >
      Every focused note shows a recall block. Producing the answer beats
      re-reading; FSRS schedules each cloze at the optimal moment to keep
      retention high without rote repetition.
    </p>
    <Link
      to="/about"
      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-transform hover:translate-y-[-1px]"
      style={{ background: 'var(--accent)', color: 'var(--paper)' }}
    >
      Read the transparency report <ChevronRight className="w-3 h-3" />
    </Link>
  </section>
);

interface AdminPanelProps {
  statsGeneratedAt?: string;
  onRefreshStats: () => Promise<void>;
}

const AdminPanel: React.FC<AdminPanelProps> = ({ statsGeneratedAt, onRefreshStats }) => {
  const [refreshing, setRefreshing] = useState(false);
  return (
    <section className="space-y-4">
      <div
        className="p-5 rounded-2xl"
        style={{
          background: 'var(--accent-soft)',
          border: '1px solid var(--hairline)',
        }}
      >
        <div className="flex items-center gap-2 mb-2">
          <Shield className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          <h3
            className="font-semibold text-sm"
            style={{ color: 'var(--ink-strong)' }}
          >
            Admin tools
          </h3>
        </div>
        <p
          className="text-xs leading-relaxed"
          style={{ color: 'var(--ink)' }}
        >
          Demo mode is off — paywall, free-tier limit, and login gating are
          bypassed for this build (<code>VITE_DEV_ADMIN</code> /{' '}
          <code>npm run dev</code>).
        </p>
        {statsGeneratedAt && (
          <p
            className="font-mono text-[10px] uppercase tracking-widest mt-3"
            style={{ color: 'var(--ink-faint)' }}
          >
            Bridge: {new Date(statsGeneratedAt).toLocaleString()}
          </p>
        )}
        <button
          onClick={async () => {
            setRefreshing(true);
            try {
              await onRefreshStats();
            } finally {
              setRefreshing(false);
            }
          }}
          className="mt-3 w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold transition-colors hover:bg-[var(--paper-elevated)]"
          style={{
            background: 'var(--paper-raised)',
            color: 'var(--ink-strong)',
            border: '1px solid var(--hairline)',
          }}
        >
          <RefreshCw className={cn('w-3.5 h-3.5', refreshing && 'animate-spin')} />
          {refreshing ? 'Refreshing…' : 'Refresh library stats'}
        </button>
      </div>
      <DataImporter />
    </section>
  );
};

const EmptyHint: React.FC<{ message: string; cta: string; href: string }> = ({
  message,
  cta,
  href,
}) => (
  <div
    className="p-4 rounded-xl text-xs leading-relaxed"
    style={{
      border: '1px dashed var(--hairline-strong)',
      color: 'var(--ink-muted)',
    }}
  >
    <p>{message}</p>
    <Link
      to={href}
      className="mt-3 inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest hover:underline"
      style={{ color: 'var(--accent)' }}
    >
      {cta} <ChevronRight className="w-3 h-3" />
    </Link>
  </div>
);
