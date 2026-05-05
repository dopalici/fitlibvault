import React, { useState, useMemo, useEffect, useRef } from 'react';
import { KnowledgeGraph } from '../components/KnowledgeGraph';
import { CitationCard } from '../components/CitationCard';
import { nodeService } from '../services/nodeService';
import { seedDatabase } from '../lib/seed';
import { NodeData, GraphNode, GraphLink } from '../types';
import { PremiumPaywall } from '../components/PremiumPaywall';
import { verifySubscription } from '../lib/stripeService';
import { auth } from '../lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { 
  X, 
  Search, 
  Filter, 
  BookOpen, 
  ChevronRight,
  ChevronLeft,
  Download,
  Share2,
  Bookmark,
  Database,
  Network,
  Lock
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '../lib/utils';
import { buildWikilinkResolver, convertWikilinksToMarkdown } from '../lib/wikilinks';

interface ContentHeading {
  id: string;
  title: string;
  level: number;
}

function normalizeHeadingId(value: string): string {
  return value.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-');
}

function headingText(children: React.ReactNode): string {
  return React.Children.toArray(children)
    .map((child) => (typeof child === 'string' ? child : ''))
    .join(' ')
    .trim();
}

export const Library: React.FC = () => {
  const FREE_NODE_LIMIT = 5;
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearchQuery, setDebouncedSearchQuery] = useState('');
  const [activeSeries, setActiveSeries] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'graph' | 'cards'>('graph');
  const [isPremium, setIsPremium] = useState(false);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [showPaywall, setShowPaywall] = useState(false);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedSearchQuery(searchQuery.trim());
    }, 300);
    return () => window.clearTimeout(timeoutId);
  }, [searchQuery]);

  useEffect(() => {
    const fetchNodes = async () => {
      setIsLoading(true);
      setLoadError(null);
      try {
        const data = await nodeService.searchNodes({
          search: debouncedSearchQuery || undefined,
          series: activeSeries || undefined,
        });
        setNodes(data);
      } catch (error) {
        console.error('Error loading nodes:', error);
        setLoadError('Unable to load library content right now.');
      } finally {
        setIsLoading(false);
      }
    };
    fetchNodes();
  }, [debouncedSearchQuery, activeSeries]);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (!user) {
        setCurrentUserId(null);
        setIsPremium(false);
        return;
      }

      setCurrentUserId(user.uid);
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
    // Refresh
    const data = await nodeService.getAllNodes();
    setNodes(data);
  };

  const filteredNodes = useMemo(() => nodes, [nodes]);

  const graphData = useMemo(() => {
    const graphNodes: GraphNode[] = filteredNodes.map(n => ({
      id: n.id,
      title: n.title,
      series: n.series,
      credibilityScore: n.credibilityScore,
      citationCount: n.citationCount
    }));

    const links: GraphLink[] = [];
    filteredNodes.forEach(node => {
      if (node.links) {
        node.links.forEach(targetId => {
          if (filteredNodes.find(fn => fn.id === targetId)) {
            links.push({
              source: node.id,
              target: targetId,
              strength: 1
            });
          }
        });
      }
    });

    return { nodes: graphNodes, links };
  }, [filteredNodes]);

  const [selectedNodeDetail, setSelectedNodeDetail] = useState<NodeData | null>(null);
  const drawerContentRef = useRef<HTMLDivElement | null>(null);
  const wikilinkResolver = useMemo(() => buildWikilinkResolver(nodes), [nodes]);
  const renderedMarkdown = useMemo(() => {
    if (!selectedNodeDetail) {
      return '';
    }
    return convertWikilinksToMarkdown(selectedNodeDetail.content, wikilinkResolver);
  }, [selectedNodeDetail, wikilinkResolver]);
  const accessibleNodes = useMemo(
    () => (isPremium ? filteredNodes : filteredNodes.slice(0, FREE_NODE_LIMIT)),
    [filteredNodes, isPremium]
  );
  const selectedNodeIndex = useMemo(
    () => filteredNodes.findIndex((node) => node.id === selectedNodeId),
    [filteredNodes, selectedNodeId]
  );
  const contentHeadings = useMemo<ContentHeading[]>(() => {
    if (!selectedNodeDetail?.content) return [];
    return selectedNodeDetail.content
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.startsWith('#'))
      .map((line) => {
        const level = line.match(/^#+/)?.[0].length || 1;
        const title = line.replace(/^#+\s*/, '').trim();
        const id = normalizeHeadingId(title);
        return { id, title, level };
      })
      .filter((heading) => heading.title.length > 0 && heading.level <= 3);
  }, [selectedNodeDetail]);

  const handleNodeAccess = (nodeId: string) => {
    if (!isPremium && !accessibleNodes.some((node) => node.id === nodeId)) {
      setShowPaywall(true);
      return;
    }
    setSelectedNodeId(nodeId);
  };
  const handleRelativeNavigation = (direction: -1 | 1) => {
    if (selectedNodeIndex < 0) return;
    const nextNode = filteredNodes[selectedNodeIndex + direction];
    if (nextNode) {
      handleNodeAccess(nextNode.id);
    }
  };
  const jumpToHeading = (headingId: string) => {
    if (!drawerContentRef.current) return;
    const target = drawerContentRef.current.querySelector(`#${headingId}`);
    if (target instanceof HTMLElement) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  useEffect(() => {
    if (selectedNodeId) {
      const fetchDetail = async () => {
        const detail = await nodeService.getNodeById(selectedNodeId);
        setSelectedNodeDetail(detail);
      };
      fetchDetail();
    } else {
      setSelectedNodeDetail(null);
    }
  }, [selectedNodeId]);

  useEffect(() => {
    if (!selectedNodeDetail?.links?.length) return;
    nodeService.prefetchNodes(selectedNodeDetail.links).catch((error) => {
      console.warn('Failed to prefetch linked nodes:', error);
    });
  }, [selectedNodeDetail]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      
      {/* SIDEBAR: Search & Filters */}
      <div className="w-80 border-r border-slate-800 flex flex-col bg-slate-900/20 backdrop-blur-md">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center font-black text-xl italic">F</div>
            <h1 className="text-xl font-bold tracking-tight">FitLib <span className="text-blue-500">Explorer</span></h1>
          </div>

          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search library..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm focus:border-blue-500 outline-none transition-all"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-widest px-1">
              <span>Categories</span>
              <Filter className="w-3 h-3" />
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { id: 'A', label: 'Foundational' },
                { id: 'B', label: 'Resistance' },
                { id: 'C', label: 'Nutrition' },
                { id: 'E', label: 'Cardio' },
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => setActiveSeries(activeSeries === cat.id ? null : cat.id)}
                  className={cn(
                    "px-3 py-2 rounded-lg text-[10px] font-bold text-left transition-all border",
                    activeSeries === cat.id 
                      ? "bg-blue-600 border-blue-500 text-white" 
                      : "bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700"
                  )}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-2">
          {isLoading ? (
            <div className="flex flex-col gap-2 animate-pulse">
               {[1,2,3,4,5].map(i => <div key={i} className="h-10 bg-slate-800 rounded-lg" />)}
            </div>
          ) : (
            <>
              <div className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 px-1">Related Topics</div>
              <div className="space-y-2">
                {filteredNodes.length === 0 && (
                  <div className="p-4 text-center">
                    <p className="text-xs text-slate-500 mb-4">
                      {loadError || 'No content found in database.'}
                    </p>
                    <button 
                      onClick={handleSeed}
                      className="flex items-center gap-2 px-3 py-2 bg-blue-600 rounded-lg text-[10px] font-bold mx-auto hover:bg-blue-700 transition-colors"
                    >
                      <Database className="w-3 h-3" /> Seed Sample Data
                    </button>
                  </div>
                )}
                {filteredNodes.map(node => {
                  const isLocked = !isPremium && !accessibleNodes.some((n) => n.id === node.id);
                  return (
                    <button
                      key={node.id}
                      onClick={() => handleNodeAccess(node.id)}
                      className={cn(
                        "w-full text-left p-3 rounded-xl border transition-all flex items-center justify-between group",
                        selectedNodeId === node.id
                          ? "bg-blue-600/10 border-blue-500/50 text-blue-400"
                          : "bg-transparent border-transparent text-slate-400 hover:bg-slate-900/50",
                        isLocked && "opacity-50"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-1.5 h-1.5 rounded-full shrink-0",
                          node.series === 'A' ? 'bg-blue-500' :
                          node.series === 'B' ? 'bg-green-500' :
                          node.series === 'C' ? 'bg-orange-500' : 'bg-red-500'
                        )} />
                        <span className="text-sm font-medium truncate">{node.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {isLocked && <Lock className="w-3 h-3 text-blue-400" />}
                        <ChevronRight className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                      </div>
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </div>
      </div>

      {/* MAIN: Area */}
      <div className="flex-1 relative flex flex-col">
        {/* Header Bar */}
        <div className="h-16 border-b border-slate-800 bg-slate-950/50 backdrop-blur-md flex items-center justify-between px-8 shrink-0">
          <div className="flex items-center gap-1 bg-slate-900 rounded-lg p-1">
            <button 
              onClick={() => setViewMode('graph')}
              className={cn(
                "px-4 py-1.5 rounded-md text-xs font-bold transition-all",
                viewMode === 'graph' ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"
              )}
            >
              Graph View
            </button>
            <button 
              onClick={() => setViewMode('cards')}
              className={cn(
                "px-4 py-1.5 rounded-md text-xs font-bold transition-all",
                viewMode === 'cards' ? "bg-blue-600 text-white shadow-lg" : "text-slate-500 hover:text-slate-300"
              )}
            >
              Card View
            </button>
          </div>
          
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest hidden md:block">
            {filteredNodes.length} Topics matching current filters
          </div>
        </div>

        <div className="flex-1 relative overflow-hidden">
          {viewMode === 'graph' ? (
            <KnowledgeGraph 
              nodes={graphData.nodes} 
              links={graphData.links} 
              onNodeClick={handleNodeAccess}
            />
          ) : (
            <div className="h-full overflow-y-auto p-8 bg-slate-950 scroll-smooth">
              <div className="max-w-6xl mx-auto grid grid-cols-1 gap-6">
                {filteredNodes.length === 0 && (
                  <div className="p-8 border border-slate-800 rounded-xl text-center text-slate-400">
                    {loadError || 'No results match your current filters.'}
                  </div>
                )}
                {filteredNodes.map((node, i) => {
                  const isLocked = !isPremium && !accessibleNodes.some((n) => n.id === node.id);
                  return (
                    <motion.div
                      key={node.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      onClick={() => handleNodeAccess(node.id)}
                      className={cn(
                        "p-6 bg-slate-900/50 border border-slate-800 rounded-2xl hover:border-blue-500/50 transition-all cursor-pointer group",
                        isLocked && "opacity-60"
                      )}
                    >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "w-3 h-3 rounded-full shadow-[0_0_8px_rgba(59,130,246,0.5)]",
                          node.series === 'A' ? 'bg-blue-500' :
                          node.series === 'B' ? 'bg-green-500' :
                          node.series === 'C' ? 'bg-orange-500' : 'bg-red-500'
                        )} />
                        <div>
                          <h3 className="font-bold text-xl group-hover:text-blue-400 transition-colors">{node.title}</h3>
                          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Series {node.series}</span>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <span className="text-xl font-black text-white">{Math.round(node.credibilityScore * 100)}%</span>
                        <span className="text-[10px] text-slate-600 font-bold uppercase">Credibility</span>
                      </div>
                    </div>
                    
                    <p className="text-sm text-slate-400 line-clamp-2 mb-4 leading-relaxed">
                      {node.content.replace(/[#*`]/g, '').slice(0, 150)}...
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        {node.tags && node.tags.slice(0, 3).map(tag => (
                          <span key={tag} className="px-2 py-0.5 bg-slate-800 rounded text-[10px] text-slate-500">#{tag}</span>
                        ))}
                      </div>
                      <span className="flex items-center gap-1 text-[10px] font-bold text-blue-500 uppercase group-hover:translate-x-1 transition-transform">
                        {isLocked && <Lock className="w-3 h-3" />}
                        Read Full Research <ChevronRight className="w-3 h-3" />
                      </span>
                    </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {viewMode === 'graph' && (
          <div className="absolute bottom-8 left-8 flex gap-4">
            <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 p-4 rounded-2xl flex items-center gap-6 shadow-2xl">
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Nodes Found</span>
                <span className="text-lg font-black text-white">{filteredNodes.length}</span>
              </div>
              <div className="w-px h-8 bg-slate-800" />
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">Ave. Credibility</span>
                <span className="text-lg font-black text-green-500">
                  {filteredNodes.length > 0 
                    ? `${Math.round((filteredNodes.reduce((acc, n) => acc + n.credibilityScore, 0) / filteredNodes.length) * 100)}%`
                    : '-%'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* DRAWER: Node Content */}
      <AnimatePresence>
        {selectedNodeDetail && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="absolute top-0 right-0 w-full md:w-[600px] h-full bg-slate-900/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl z-50 flex flex-col"
          >
            <div className="flex items-center justify-between p-6 border-b border-slate-800">
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => setSelectedNodeId(null)}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
                <div>
                  <h2 className="text-lg font-bold">{selectedNodeDetail.title}</h2>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-blue-500 uppercase tracking-widest underline decoration-2 underline-offset-4">
                      Series {selectedNodeDetail.series}
                    </span>
                    <span className="text-[10px] text-slate-500">•</span>
                    <span className="text-[10px] text-green-500 font-bold uppercase tracking-widest">
                       {Math.round(selectedNodeDetail.credibilityScore * 100)}% Credibility
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2">
                 <button
                   onClick={() => handleRelativeNavigation(-1)}
                   disabled={selectedNodeIndex <= 0}
                   className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 disabled:opacity-40"
                 >
                   <ChevronLeft className="w-5 h-5" />
                 </button>
                 <button
                   onClick={() => handleRelativeNavigation(1)}
                   disabled={selectedNodeIndex === -1 || selectedNodeIndex >= filteredNodes.length - 1}
                   className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 disabled:opacity-40"
                 >
                   <ChevronRight className="w-5 h-5" />
                 </button>
                 <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"><Bookmark className="w-5 h-5" /></button>
                 <button className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400"><Share2 className="w-5 h-5" /></button>
              </div>
            </div>

            <div ref={drawerContentRef} className="flex-1 overflow-y-auto p-10">
              {contentHeadings.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">In this file</h3>
                  <div className="flex flex-wrap gap-2">
                    {contentHeadings.slice(0, 12).map((heading) => (
                      <button
                        key={heading.id}
                        onClick={() => jumpToHeading(heading.id)}
                        className={cn(
                          "text-xs px-2 py-1 rounded border transition-colors",
                          heading.level === 1
                            ? "border-blue-500/50 text-blue-300"
                            : "border-slate-700 text-slate-400 hover:text-slate-200"
                        )}
                      >
                        {heading.title}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="markdown-body prose prose-invert prose-blue max-w-none mb-16">
                 <ReactMarkdown
                   components={{
                    h1: ({ children }) => {
                      const id = normalizeHeadingId(headingText(children));
                      return <h1 id={id}>{children}</h1>;
                    },
                    h2: ({ children }) => {
                      const id = normalizeHeadingId(headingText(children));
                      return <h2 id={id}>{children}</h2>;
                    },
                    h3: ({ children }) => {
                      const id = normalizeHeadingId(headingText(children));
                      return <h3 id={id}>{children}</h3>;
                    },
                    a: ({ href, children }) => {
                      if (href?.startsWith('fitlib://node/')) {
                        const nodeId = decodeURIComponent(href.replace('fitlib://node/', ''));
                        return (
                          <button
                            onClick={() => handleNodeAccess(nodeId)}
                            className="text-blue-400 underline underline-offset-2 hover:text-blue-300"
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
                          className="text-blue-400 underline underline-offset-2 hover:text-blue-300"
                        >
                          {children}
                        </a>
                      );
                    },
                   }}
                 >
                   {renderedMarkdown}
                 </ReactMarkdown>
              </div>

              {/* Related Topics Interlinks */}
              {selectedNodeDetail.links && selectedNodeDetail.links.length > 0 && (
                <div className="mb-16">
                  <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
                    <Network className="w-5 h-5 text-blue-400" />
                    Related Research
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {selectedNodeDetail.links.map(linkId => {
                      const linkedNode = nodes.find(n => n.id === linkId);
                      if (!linkedNode) return null;
                      return (
                        <button
                          key={linkId}
                          onClick={() => handleNodeAccess(linkId)}
                          className="flex items-center justify-between p-4 bg-slate-800/40 border border-slate-700/50 rounded-xl hover:border-blue-500/50 transition-all group"
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              "w-1.5 h-1.5 rounded-full",
                              linkedNode.series === 'A' ? 'bg-blue-500' :
                              linkedNode.series === 'B' ? 'bg-green-500' :
                              linkedNode.series === 'C' ? 'bg-orange-500' : 'bg-red-500'
                            )} />
                            <span className="text-sm font-semibold text-slate-200 group-hover:text-blue-400">{linkedNode.title}</span>
                          </div>
                          <ChevronRight className="w-4 h-4 text-slate-600 group-hover:translate-x-1 transition-transform" />
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {selectedNodeDetail.citations && selectedNodeDetail.citations.length > 0 && (
                <div className="space-y-8">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                       <BookOpen className="w-5 h-5 text-blue-400" />
                       Research Citations
                    </h3>
                    <span className="text-xs text-slate-500">{selectedNodeDetail.citations.length} sources confirmed</span>
                  </div>
                  <div className="grid grid-cols-1 gap-6">
                    {selectedNodeDetail.citations.map(citation => (
                      <CitationCard key={citation.id} citation={citation} />
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 bg-slate-950/50 border-t border-slate-800 flex justify-between items-center">
               <div className="flex gap-2">
                 {selectedNodeDetail.tags && selectedNodeDetail.tags.map(tag => (
                   <span key={tag} className="px-2 py-1 bg-slate-800 rounded text-[10px] text-slate-400 font-medium">#{tag}</span>
                 ))}
               </div>
               <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors">
                 <Download className="w-4 h-4" /> Download PDF
               </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {showPaywall && (
        <PremiumPaywall
          userId={currentUserId || undefined}
          onClose={() => setShowPaywall(false)}
        />
      )}
    </div>
  );
};

