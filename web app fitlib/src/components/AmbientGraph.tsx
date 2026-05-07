/**
 * Ambient knowledge-graph background.
 *
 * Goal: the graph is *behind* the reader, dim and slow, with the current node
 * and its 1-hop neighbourhood lit up. It informs without distracting (Sweller's
 * CLT — extraneous load is the enemy).
 *
 * Performance:
 *   - Force simulation ticks once on mount until alphaMin, then we freeze.
 *   - Frozen positions are cached by node-set hash (so coming back to the
 *     same set of nodes is instant).
 *   - A tiny per-frame perlin-ish offset gives the "drift" without re-running
 *     physics. CPU stays near zero.
 *
 * Use this alongside the existing `KnowledgeGraph` component. `KnowledgeGraph`
 * stays for the dedicated graph route; `AmbientGraph` is for the reader.
 */

import React, { useEffect, useMemo, useRef } from 'react';
import * as d3 from 'd3';
import type { GraphNode, GraphLink } from '../types';

interface Props {
  nodes: GraphNode[];
  links: GraphLink[];
  /** Active node id (lit up). */
  activeId?: string | null;
  /** Allow user interaction (zoom/pan/click). False keeps it as a wallpaper. */
  interactive?: boolean;
  onNodeClick?: (id: string) => void;
  /** Multiplier for visual intensity. 0.4 reads well behind text. */
  intensity?: number;
}

const SERIES_COLOR: Record<string, string> = {
  A: '#7DF9FF',
  B: '#5CFFCB',
  C: '#FFC857',
  D: '#FF7AC6',
  E: '#FF5C8A',
  Other: '#AB7DF7',
};

function positionsKey(nodes: GraphNode[], links: GraphLink[]): string {
  // Quick set-hash so we cache per-graph-shape, not per-render.
  const ids = nodes.map((n) => n.id).sort().join('|');
  const ls = links
    .map((l) => `${typeof l.source === 'string' ? l.source : (l.source as GraphNode).id}->${typeof l.target === 'string' ? l.target : (l.target as GraphNode).id}`)
    .sort()
    .join('|');
  let h = 0;
  const s = ids + '||' + ls;
  for (let i = 0; i < s.length; i++) h = ((h << 5) - h + s.charCodeAt(i)) | 0;
  return `fitlib-graph-pos:${h}`;
}

interface FrozenPos { id: string; x: number; y: number; }

function loadFrozen(key: string): FrozenPos[] | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) as FrozenPos[] : null;
  } catch { return null; }
}

function saveFrozen(key: string, positions: FrozenPos[]): void {
  if (typeof window === 'undefined') return;
  try { window.localStorage.setItem(key, JSON.stringify(positions)); } catch { /* quota — fine */ }
}

export const AmbientGraph: React.FC<Props> = ({
  nodes,
  links,
  activeId,
  interactive = false,
  onNodeClick,
  intensity = 0.4,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const driftRef = useRef<number>(0);

  const cacheKey = useMemo(() => positionsKey(nodes, links), [nodes, links]);

  // Adjacency for 1-hop highlight.
  const neighbours = useMemo(() => {
    const map = new Map<string, Set<string>>();
    nodes.forEach((n) => map.set(n.id, new Set()));
    links.forEach((l) => {
      const s = typeof l.source === 'string' ? l.source : (l.source as GraphNode).id;
      const t = typeof l.target === 'string' ? l.target : (l.target as GraphNode).id;
      map.get(s)?.add(t);
      map.get(t)?.add(s);
    });
    return map;
  }, [nodes, links]);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;
    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const cached = loadFrozen(cacheKey);
    let positioned: GraphNode[];
    if (cached && cached.length === nodes.length) {
      const byId = new Map(cached.map((p) => [p.id, p]));
      positioned = nodes.map((n) => ({ ...n, x: byId.get(n.id)?.x ?? width / 2, y: byId.get(n.id)?.y ?? height / 2 }));
    } else {
      const sim = d3.forceSimulation<GraphNode>(nodes.map((n) => ({ ...n })))
        .force('link', d3.forceLink<GraphNode, GraphLink>(links).id((d) => d.id).distance(80))
        .force('charge', d3.forceManyBody().strength(-180))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(12))
        .stop();
      // Run synchronously to a stable layout, then freeze.
      const ticks = Math.min(300, Math.ceil(Math.log(sim.alphaMin()) / Math.log(1 - sim.alphaDecay())));
      for (let i = 0; i < ticks; i++) sim.tick();
      positioned = sim.nodes() as GraphNode[];
      saveFrozen(cacheKey, positioned.map((p) => ({ id: p.id, x: p.x ?? 0, y: p.y ?? 0 })));
    }

    const root = svg.append('g').attr('class', 'ambient-root');

    if (interactive) {
      const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.4, 2]).on('zoom', (e) => {
        root.attr('transform', e.transform.toString());
      });
      svg.call(zoom);
    }

    // Edges first.
    const edge = root.append('g')
      .attr('stroke', '#7DF9FF')
      .attr('stroke-opacity', 0.10 * intensity)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', 1);

    const node = root.append('g')
      .selectAll('circle')
      .data(positioned, (d: any) => d.id)
      .join('circle')
      .attr('r', (d: any) => 2.5 + Math.min(6, (d.credibilityScore || 0.5) * 6))
      .attr('fill', (d: any) => SERIES_COLOR[d.series] || SERIES_COLOR.Other)
      .attr('opacity', 0.18 * intensity)
      .attr('stroke', 'transparent')
      .attr('stroke-width', 0)
      .style('cursor', interactive ? 'pointer' : 'default')
      .on('click', (_e, d: any) => interactive && onNodeClick?.(d.id));

    // Apply active highlight.
    function applyHighlight(id: string | null | undefined) {
      const hood = id ? neighbours.get(id) ?? new Set<string>() : new Set<string>();
      node
        .attr('opacity', (d: any) => {
          if (!id) return 0.18 * intensity;
          if (d.id === id) return 1;
          if (hood.has(d.id)) return 0.7;
          return 0.08 * intensity;
        })
        .attr('stroke', (d: any) => (d.id === id ? '#FFFFFF' : 'transparent'))
        .attr('stroke-width', (d: any) => (d.id === id ? 1.5 : 0))
        .attr('r', (d: any) => {
          const base = 2.5 + Math.min(6, (d.credibilityScore || 0.5) * 6);
          return d.id === id ? base * 1.8 : base;
        });
      edge.attr('stroke-opacity', (d: any) => {
        if (!id) return 0.10 * intensity;
        const s = typeof d.source === 'string' ? d.source : d.source.id;
        const t = typeof d.target === 'string' ? d.target : d.target.id;
        return s === id || t === id ? 0.55 : 0.04 * intensity;
      });
    }

    applyHighlight(activeId);

    // Drift loop. Tiny sinusoidal wobble on the root group, never re-physics.
    let raf = 0;
    const animate = () => {
      driftRef.current += 0.0007;
      const dx = Math.sin(driftRef.current) * 4;
      const dy = Math.cos(driftRef.current * 0.7) * 3;
      root.attr('transform', `translate(${dx}, ${dy})`);
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);

    // Position the static elements once (we won't tick again).
    edge
      .attr('x1', (d: any) => (typeof d.source === 'string' ? positioned.find((p) => p.id === d.source)?.x ?? 0 : d.source.x))
      .attr('y1', (d: any) => (typeof d.source === 'string' ? positioned.find((p) => p.id === d.source)?.y ?? 0 : d.source.y))
      .attr('x2', (d: any) => (typeof d.target === 'string' ? positioned.find((p) => p.id === d.target)?.x ?? 0 : d.target.x))
      .attr('y2', (d: any) => (typeof d.target === 'string' ? positioned.find((p) => p.id === d.target)?.y ?? 0 : d.target.y));
    node
      .attr('cx', (d: any) => d.x)
      .attr('cy', (d: any) => d.y);

    // React to active changes without tearing down the layout.
    return () => cancelAnimationFrame(raf);
  }, [cacheKey, nodes, links, interactive, intensity, onNodeClick, neighbours, activeId]);

  return (
    <div ref={containerRef} className="absolute inset-0 pointer-events-none">
      <svg ref={svgRef} className="w-full h-full" aria-hidden />
    </div>
  );
};
