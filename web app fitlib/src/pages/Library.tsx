/**
 * Library — the canonical read/learn surface.
 *
 * Layout (Quartz × Andy Matuschak):
 *
 *   ┌───────────┬────────────────────────────────────┬───────────────┐
 *   │           │                                    │               │
 *   │  Explorer │  Stacked reader (panels scroll →) │  Sidekick     │
 *   │ (folders) │   ⮕                                │  (TOC, links, │
 *   │           │  Reader / Graph / Cards mode tabs  │   local graph)│
 *   │           │                                    │               │
 *   └───────────┴────────────────────────────────────┴───────────────┘
 *
 * Demo mode is fully off in dev / VITE_DEV_ADMIN builds — the previous
 * 5-node free-tier limit + paywall are bypassed for the owner. The reader
 * surface uses the new paper-on-ink theme tokens; no ambient glow.
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { ChevronRight, Lock, Network, Layers, ScrollText } from 'lucide-react';
import { KnowledgeGraph } from '../components/KnowledgeGraph';
import { NoteReader } from '../components/NoteReader';
import { StackedReader } from '../components/StackedReader';
import { LibraryExplorer } from '../components/LibraryExplorer';
import { nodeService } from '../services/nodeService';
import { seedDatabase } from '../lib/seed';
import { NodeData, GraphNode, GraphLink } from '../types';
import { PremiumPaywall } from '../components/PremiumPaywall';
import { verifySubscription } from '../lib/stripeService';
import { isAdminUser } from '../lib/admin';
import { env } from '../lib/env';
import { auth } from '../lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { cn } from '../lib/utils';
import { seriesTone } from '../lib/libraryStats';

type ViewMode = 'reader' | 'graph' | 'cards';

export const Library: React.FC = () => {
  const FREE_NODE_LIMIT = 5;
  const [searchParams] = useSearchParams();

  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState(() => searchParams.get('search') || '');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState(
    () => searchParams.get('search') || ''
  );
  const [activeSeries, setActiveSeries] = useState<string | null>(
    () => searchParams.get('series')
  );
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('reader');

  const [isPremium, setIsPremium] = useState<boolean>(env.devAdmin);
  const [isAdmin, setIsAdmin] = useState<boolean>(env.devAdmin);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);

  useEffect(() => {
    const t = window.setTimeout(() => setDebouncedSearchQuery(searchQuery.trim()), 300);
    return () => window.clearTimeout(t);
  }, [searchQuery]);

  useEffect(() => {
    let cancelled = false;
    const fetchNodes = async () => {
      setIsLoading(true);
      setLoadError(null);
      try {
        const data = await nodeService.searchNodes({
          search: debouncedSearchQuery || undefined,
          series: activeSeries || undefined,
        });
        if (!cancelled) setNodes(data);
      } catch (error) {
        console.error('Error loading nodes:', error);
        if (!cancelled) setLoadError('Unable to load library content right now.');
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };
    fetchNodes();
    return () => {
      cancelled = true;
    };
  }, [debouncedSearchQuery, activeSeries]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        setCurrentUserId(null);
        setIsAdmin(env.devAdmin);
        setIsPremium(env.devAdmin);
        return;
      }
      setCurrentUserId(user.uid);
      const admin = isAdminUser(user);
      setIsAdmin(admin);
      if (admin) {
        setIsPremium(true);
        return;
      }
      try {
        const status = await verifySubscription(user.uid);
        setIsPremium(status.premium);
      } catch (error) {
        console.warn('Failed to load subscription status:', error);
        setIsPremium(false);
      }
    });
    return () => unsubscribe();
  }, []);

  const handleSeed = async () => {
    await seedDatabase();
    const data = await nodeService.getAllNodes();
    setNodes(data);
  };

  const filteredNodes = useMemo(() => nodes, [nodes]);
  const hasFullAccess = isPremium || isAdmin;

  const accessibleNodes = useMemo(
    () => (hasFullAccess ? filteredNodes : filteredNodes.slice(0, FREE_NODE_LIMIT)),
    [filteredNodes, hasFullAccess]
  );

  const lockedIds = useMemo(() => {
    if (hasFullAccess) return new Set<string>();
    const allowed = new Set(accessibleNodes.map((n) => n.id));
    return new Set(filteredNodes.filter((n) => !allowed.has(n.id)).map((n) => n.id));
  }, [filteredNodes, accessibleNodes, hasFullAccess]);

  const graphData = useMemo(() => {
    const graphNodes: GraphNode[] = filteredNodes.map((n) => ({
      id: n.id,
      title: n.title,
      series: n.series,
      credibilityScore: n.credibilityScore,
      citationCount: n.citationCount,
    }));
    const ids = new Set(filteredNodes.map((n) => n.id));
    const links: GraphLink[] = [];
    filteredNodes.forEach((node) => {
      node.links?.forEach((targetId) => {
        if (ids.has(targetId)) {
          links.push({ source: node.id, target: targetId, strength: 1 });
        }
      });
    });
    return { nodes: graphNodes, links };
  }, [filteredNodes]);

  const [selectedNodeDetail, setSelectedNodeDetail] = useState<NodeData | null>(null);

  const handleNodeAccess = (nodeId: string) => {
    if (!hasFullAccess && lockedIds.has(nodeId)) {
      setShowPaywall(true);
      return;
    }
    setSelectedNodeId(nodeId);
  };

  useEffect(() => {
    if (!selectedNodeId) {
      setSelectedNodeDetail(null);
      return;
    }
    const fetchDetail = async () => {
      const detail = await nodeService.getNodeById(selectedNodeId);
      setSelectedNodeDetail(detail);
    };
    fetchDetail();
  }, [selectedNodeId]);

  useEffect(() => {
    if (!selectedNodeDetail?.links?.length) return;
    nodeService.prefetchNodes(selectedNodeDetail.links).catch((error) => {
      console.warn('Failed to prefetch linked nodes:', error);
    });
  }, [selectedNodeDetail]);

  return (
    <div
      className="flex flex-1 min-h-0 overflow-hidden"
      style={{ background: 'var(--paper)' }}
    >
      <LibraryExplorer
        nodes={filteredNodes}
        selectedNodeId={selectedNodeId}
        lockedNodeIds={lockedIds}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        activeSeries={activeSeries}
        onSeriesChange={setActiveSeries}
        onSelectNode={handleNodeAccess}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <Toolbar
          mode={viewMode}
          onModeChange={setViewMode}
          totalCount={filteredNodes.length}
          isAdmin={isAdmin}
        />

        <div className="flex-1 relative overflow-hidden">
          {isLoading && filteredNodes.length === 0 ? (
            <LoadingShimmer />
          ) : filteredNodes.length === 0 ? (
            <EmptyState onSeed={handleSeed} message={loadError} />
          ) : viewMode === 'reader' ? (
            <StackedReader
              nodes={accessibleNodes}
              fetchNode={(id) => nodeService.getNodeById(id)}
              initialStack={
                selectedNodeId ? [selectedNodeId] : accessibleNodes[0] ? [accessibleNodes[0].id] : []
              }
              externalOpenNodeId={selectedNodeId}
            />
          ) : viewMode === 'graph' ? (
            <div className="absolute inset-0">
              <KnowledgeGraph
                nodes={graphData.nodes}
                links={graphData.links}
                onNodeClick={handleNodeAccess}
              />
              <GraphStats count={filteredNodes.length} nodes={filteredNodes} />
            </div>
          ) : (
            <CardsView
              nodes={filteredNodes}
              lockedIds={lockedIds}
              onSelect={handleNodeAccess}
            />
          )}
        </div>
      </div>

      {viewMode !== 'reader' && selectedNodeDetail && (
        <div className="hidden xl:block w-[640px] shrink-0 h-full overflow-hidden p-4"
          style={{ borderLeft: '1px solid var(--hairline)', background: 'var(--paper)' }}
        >
          <NoteReader
            node={selectedNodeDetail}
            index={accessibleNodes}
            isFocused
            onClose={() => setSelectedNodeId(null)}
            onWikilinkOpen={(_fromId, targetId) => handleNodeAccess(targetId)}
          />
        </div>
      )}

      {showPaywall && (
        <PremiumPaywall
          userId={currentUserId || undefined}
          onClose={() => setShowPaywall(false)}
        />
      )}
    </div>
  );
};

interface ToolbarProps {
  mode: ViewMode;
  onModeChange: (m: ViewMode) => void;
  totalCount: number;
  isAdmin: boolean;
}

const Toolbar: React.FC<ToolbarProps> = ({ mode, onModeChange, totalCount, isAdmin }) => (
  <div
    className="h-14 flex items-center justify-between px-6"
    style={{ borderBottom: '1px solid var(--hairline)', background: 'var(--paper)' }}
  >
    <div
      className="flex items-center gap-1 rounded-lg p-1"
      style={{ background: 'var(--paper-raised)', border: '1px solid var(--hairline)' }}
    >
      {(
        [
          { id: 'reader', label: 'Reader', icon: ScrollText },
          { id: 'graph', label: 'Graph', icon: Network },
          { id: 'cards', label: 'Cards', icon: Layers },
        ] as const
      ).map((opt) => {
        const isActive = mode === opt.id;
        return (
          <button
            key={opt.id}
            onClick={() => onModeChange(opt.id)}
            className="px-3 py-1.5 rounded-md text-xs font-semibold inline-flex items-center gap-1.5 transition-colors"
            style={{
              background: isActive ? 'var(--accent)' : 'transparent',
              color: isActive ? 'var(--paper)' : 'var(--ink-muted)',
            }}
          >
            <opt.icon className="w-3.5 h-3.5" />
            {opt.label}
          </button>
        );
      })}
    </div>
    <div className="flex items-center gap-3">
      {isAdmin && (
        <span
          className="hidden md:inline-flex font-mono text-[10px] uppercase tracking-widest items-center gap-1.5 px-2 py-1 rounded-full"
          style={{
            background: 'var(--accent-soft)',
            color: 'var(--accent)',
            border: '1px solid var(--hairline)',
          }}
        >
          Admin
        </span>
      )}
      <span
        className="hidden md:inline font-mono text-[10px] uppercase tracking-widest"
        style={{ color: 'var(--ink-faint)' }}
      >
        {totalCount} matching
      </span>
    </div>
  </div>
);

const LoadingShimmer: React.FC = () => (
  <div className="p-6 flex flex-col gap-3 animate-pulse">
    {[1, 2, 3, 4, 5].map((i) => (
      <div
        key={i}
        className="h-12 rounded-xl"
        style={{ background: 'var(--paper-raised)' }}
      />
    ))}
  </div>
);

const EmptyState: React.FC<{ onSeed: () => void; message: string | null }> = ({ onSeed, message }) => (
  <div
    className="h-full w-full flex items-center justify-center p-8"
    style={{ background: 'var(--paper)' }}
  >
    <div className="max-w-md text-center">
      <p className="mb-4" style={{ color: 'var(--ink-muted)' }}>
        {message || 'No notes match the current filters.'}
      </p>
      <button
        onClick={onSeed}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold"
        style={{
          background: 'var(--accent)',
          color: 'var(--paper)',
        }}
      >
        Seed sample data
      </button>
    </div>
  </div>
);

const GraphStats: React.FC<{ count: number; nodes: NodeData[] }> = ({ count, nodes }) => {
  const avgCredibility =
    nodes.length === 0
      ? 0
      : Math.round(
          (nodes.reduce((acc, n) => acc + (n.credibilityScore || 0), 0) / nodes.length) * 100
        );
  return (
    <div
      className="absolute bottom-6 left-6 flex items-center gap-5 rounded-2xl px-5 py-3"
      style={{
        background: 'var(--paper-raised)',
        border: '1px solid var(--hairline)',
      }}
    >
      <Stat label="Nodes" value={count} />
      <span className="w-px h-6" style={{ background: 'var(--hairline)' }} />
      <Stat label="Avg credibility" value={`${avgCredibility}%`} accent="var(--accent)" />
    </div>
  );
};

const Stat: React.FC<{ label: string; value: React.ReactNode; accent?: string }> = ({
  label,
  value,
  accent,
}) => (
  <div className="flex flex-col">
    <span
      className="font-mono text-[10px] uppercase tracking-widest"
      style={{ color: 'var(--ink-faint)' }}
    >
      {label}
    </span>
    <span
      className="text-base font-semibold tabular-nums"
      style={{ color: accent || 'var(--ink-strong)' }}
    >
      {value}
    </span>
  </div>
);

const CardsView: React.FC<{
  nodes: NodeData[];
  lockedIds: Set<string>;
  onSelect: (id: string) => void;
}> = ({ nodes, lockedIds, onSelect }) => (
  <div
    className="h-full overflow-y-auto p-8"
    style={{ background: 'var(--paper)' }}
  >
    <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-5">
      {nodes.map((node, i) => {
        const tone = seriesTone(node.series);
        const isLocked = lockedIds.has(node.id);
        return (
          <motion.button
            key={node.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.02, 0.6) }}
            onClick={() => onSelect(node.id)}
            className={cn(
              'group text-left p-6 rounded-2xl transition-all',
              isLocked && 'opacity-60'
            )}
            style={{
              background: 'var(--paper-raised)',
              border: '1px solid var(--hairline)',
            }}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3 min-w-0">
                <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', tone.dot)} />
                <div className="min-w-0">
                  <h3
                    className="font-semibold text-lg leading-snug"
                    style={{ color: 'var(--ink-strong)', fontFamily: 'var(--font-serif)' }}
                  >
                    {node.title}
                  </h3>
                  <p
                    className="font-mono text-[10px] uppercase tracking-widest mt-1"
                    style={{ color: 'var(--ink-faint)' }}
                  >
                    Series {node.series} · {node.id}
                  </p>
                </div>
              </div>
              <div className="text-right shrink-0">
                <div
                  className="text-base font-semibold tabular-nums"
                  style={{ color: 'var(--ink-strong)' }}
                >
                  {Math.round(node.credibilityScore * 100)}%
                </div>
                <div
                  className="font-mono text-[10px] uppercase tracking-widest"
                  style={{ color: 'var(--ink-faint)' }}
                >
                  Credibility
                </div>
              </div>
            </div>

            <p
              className="text-sm leading-relaxed line-clamp-3 mb-4"
              style={{ color: 'var(--ink)', fontFamily: 'var(--font-serif)' }}
            >
              {node.content.replace(/[#*`]/g, '').slice(0, 200)}…
            </p>

            <div className="flex items-center justify-between">
              <div className="flex flex-wrap gap-1.5">
                {node.tags?.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="font-mono text-[10px] tracking-wide px-2 py-0.5 rounded-full"
                    style={{
                      background: 'var(--paper-elevated)',
                      color: 'var(--ink-muted)',
                      border: '1px solid var(--hairline)',
                    }}
                  >
                    #{tag.split(/\s+/)[0].slice(0, 18)}
                  </span>
                ))}
              </div>
              <span
                className="inline-flex items-center gap-1 font-mono text-[10px] uppercase tracking-widest group-hover:translate-x-0.5 transition-transform"
                style={{ color: 'var(--accent)' }}
              >
                {isLocked && <Lock className="w-3 h-3" />}
                Read note <ChevronRight className="w-3 h-3" />
              </span>
            </div>
          </motion.button>
        );
      })}
    </div>
    <p
      className="text-center mt-12 text-xs"
      style={{ color: 'var(--ink-faint)' }}
    >
      <Link to="/about" style={{ color: 'var(--accent)' }} className="underline underline-offset-2">
        How learning works in FitLib →
      </Link>
    </p>
  </div>
);
