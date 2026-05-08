/**
 * NoteSidekick — the right rail beside the focused reader column.
 *
 * Quartz pattern: every page has its own little orientation panel listing
 * the in-page table of contents and the notes that link *to* it. We use
 * the same idea here, plus a tight 1-hop local graph and a recall summary.
 *
 * The whole panel is read-only and computed from data the reader already
 * has loaded, so opening / closing it never re-fetches anything.
 */

import React, { useMemo } from 'react';
import * as d3 from 'd3';
import { ChevronRight, GitBranch, ListTree, Network } from 'lucide-react';
import type { NodeData } from '../types';
import { parseNoteSections } from '../lib/noteSchema';
import {
  buildLocalGraph,
  type BacklinkIndex,
} from '../lib/backlinks';
import { cn } from '../lib/utils';

interface Props {
  focused: NodeData;
  index: NodeData[];
  backlinks: BacklinkIndex;
  onOpenNode: (id: string) => void;
}

export const NoteSidekick: React.FC<Props> = ({ focused, index, backlinks, onOpenNode }) => {
  const sections = useMemo(() => parseNoteSections(focused.content), [focused.content]);
  const headings = useMemo(() => extractHeadings(focused.content), [focused.content]);
  const linkedFrom = backlinks.get(focused.id) || [];
  const local = useMemo(
    () => buildLocalGraph(index, focused.id, backlinks, 18),
    [index, focused.id, backlinks]
  );

  return (
    <aside
      className="hidden xl:flex shrink-0 flex-col w-72 max-h-full overflow-y-auto pr-2"
      aria-label="Note sidekick"
    >
      <SidekickPanel icon={ListTree} label="On this page">
        {headings.length === 0 ? (
          <p className="text-xs leading-relaxed" style={{ color: 'var(--ink-faint)' }}>
            No subsections detected.
          </p>
        ) : (
          <ul className="space-y-1.5">
            {headings.map((h) => (
              <li key={`${h.level}-${h.text}`}>
                <span
                  className={cn(
                    'block text-xs leading-snug',
                    h.level === 2 ? 'font-medium' : 'pl-3 opacity-80'
                  )}
                  style={{
                    color: h.level === 2 ? 'var(--ink)' : 'var(--ink-muted)',
                  }}
                >
                  {h.text}
                </span>
              </li>
            ))}
          </ul>
        )}
      </SidekickPanel>

      <SidekickPanel
        icon={GitBranch}
        label="Linked from"
        trailing={`${linkedFrom.length}`}
      >
        {linkedFrom.length === 0 ? (
          <p className="text-xs leading-relaxed" style={{ color: 'var(--ink-faint)' }}>
            Nothing in the library cites this note yet.
          </p>
        ) : (
          <ul className="space-y-1">
            {linkedFrom.slice(0, 12).map((entry) => (
              <li key={entry.id}>
                <button
                  type="button"
                  onClick={() => onOpenNode(entry.id)}
                  className="group w-full flex items-center justify-between text-left text-xs leading-tight rounded-md px-2 py-1.5 transition-colors hover:bg-[var(--paper-elevated)]"
                  style={{ color: 'var(--ink)' }}
                >
                  <span className="truncate pr-2">{entry.title}</span>
                  <ChevronRight
                    className="w-3 h-3 shrink-0 group-hover:translate-x-0.5 transition-transform"
                    style={{ color: 'var(--ink-faint)' }}
                  />
                </button>
              </li>
            ))}
          </ul>
        )}
      </SidekickPanel>

      <SidekickPanel icon={Network} label="Local graph">
        <LocalGraphlet
          slice={local}
          focusId={focused.id}
          onSelect={(id) => onOpenNode(id)}
        />
      </SidekickPanel>

      <SidekickPanel label="At a glance">
        <dl className="grid grid-cols-2 gap-3 text-[11px]">
          <Stat label="Citations" value={sections.evidence.length} />
          <Stat label="Key points" value={sections.keyPoints.length} />
          <Stat label="Outgoing" value={focused.links?.length || 0} />
          <Stat label="Backlinks" value={linkedFrom.length} />
        </dl>
      </SidekickPanel>
    </aside>
  );
};

interface SidekickPanelProps {
  icon?: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  trailing?: string;
  children: React.ReactNode;
}

const SidekickPanel: React.FC<SidekickPanelProps> = ({ icon: Icon, label, trailing, children }) => (
  <section
    className="rounded-2xl px-4 py-4 mb-3 last:mb-0"
    style={{
      border: '1px solid var(--hairline)',
      background: 'var(--paper-raised)',
    }}
  >
    <header className="flex items-center justify-between mb-3">
      <h4
        className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em]"
        style={{ color: 'var(--ink-muted)' }}
      >
        {Icon && <Icon className="w-3 h-3" style={{ color: 'var(--ink-faint)' }} />}
        {label}
      </h4>
      {trailing && (
        <span
          className="text-[10px] font-mono tabular-nums"
          style={{ color: 'var(--ink-faint)' }}
        >
          {trailing}
        </span>
      )}
    </header>
    {children}
  </section>
);

const Stat: React.FC<{ label: string; value: number }> = ({ label, value }) => (
  <div
    className="rounded-lg px-3 py-2"
    style={{ background: 'var(--paper-elevated)' }}
  >
    <div
      className="text-base font-semibold tabular-nums"
      style={{ color: 'var(--ink-strong)' }}
    >
      {value}
    </div>
    <div
      className="font-mono text-[9px] uppercase tracking-widest"
      style={{ color: 'var(--ink-faint)' }}
    >
      {label}
    </div>
  </div>
);

interface LocalGraphProps {
  slice: { nodes: { id: string; title: string; series: string }[]; links: { source: string; target: string }[] };
  focusId: string;
  onSelect: (id: string) => void;
}

const LocalGraphlet: React.FC<LocalGraphProps> = ({ slice, focusId, onSelect }) => {
  const svgRef = React.useRef<SVGSVGElement>(null);

  React.useEffect(() => {
    if (!svgRef.current) return;
    if (slice.nodes.length === 0) return;

    const width = 240;
    const height = 200;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    svg.attr('viewBox', `0 0 ${width} ${height}`);

    const nodesCopy = slice.nodes.map((n) => ({ ...n })) as Array<{
      id: string;
      title: string;
      series: string;
      x?: number;
      y?: number;
      fx?: number | null;
      fy?: number | null;
    }>;
    const linksCopy = slice.links.map((l) => ({ ...l })) as Array<{ source: string | { id: string }; target: string | { id: string } }>;

    const sim = d3
      .forceSimulation(nodesCopy as any)
      .force(
        'link',
        d3
          .forceLink(linksCopy as any)
          .id((d: any) => d.id)
          .distance(45)
      )
      .force('charge', d3.forceManyBody().strength(-90))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(14))
      .stop();

    const ticks = Math.min(140, Math.ceil(Math.log(sim.alphaMin()) / Math.log(1 - sim.alphaDecay())));
    for (let i = 0; i < ticks; i++) sim.tick();

    // Neighbour map for the hover-focus effect (Quartz-style).
    const neighbours = new Map<string, Set<string>>();
    nodesCopy.forEach((n) => neighbours.set(n.id, new Set([n.id])));
    linksCopy.forEach((l: any) => {
      const sId = typeof l.source === 'object' ? l.source.id : l.source;
      const tId = typeof l.target === 'object' ? l.target.id : l.target;
      neighbours.get(sId)?.add(tId);
      neighbours.get(tId)?.add(sId);
    });

    const DIM = 0.15;
    const FADE_MS = 180;
    const baseRadius = (d: any) => (d.id === focusId ? 6.5 : 4);
    const baseFill = (d: any) => (d.id === focusId ? 'var(--accent)' : 'var(--ink-faint)');

    const root = svg.append('g');
    const lineSel = root
      .append('g')
      .selectAll('line')
      .data(linksCopy)
      .join('line')
      .attr('x1', (d: any) => d.source.x)
      .attr('y1', (d: any) => d.source.y)
      .attr('x2', (d: any) => d.target.x)
      .attr('y2', (d: any) => d.target.y)
      .attr('stroke', 'var(--hairline-strong)')
      .attr('stroke-width', 0.7);

    const circleSel = root
      .append('g')
      .selectAll('circle')
      .data(nodesCopy)
      .join('circle')
      .attr('cx', (d: any) => d.x)
      .attr('cy', (d: any) => d.y)
      .attr('r', baseRadius)
      .attr('fill', baseFill)
      .attr('stroke', (d: any) => (d.id === focusId ? 'var(--accent)' : 'transparent'))
      .attr('stroke-width', 1.2)
      .attr('opacity', (d: any) => (d.id === focusId ? 1 : 0.7))
      .style('cursor', 'pointer')
      .on('click', (_e, d: any) => onSelect(d.id))
      .on('mouseenter', (_e, d: any) => focus(d.id))
      .on('mouseleave', () => focus(null));

    // Labels hidden by default — only the focused node carries one.
    // Hover reveals labels for the hovered node + its first-degree neighbours.
    const textSel = root
      .append('g')
      .selectAll('text')
      .data(nodesCopy)
      .join('text')
      .attr('x', (d: any) => d.x + 8)
      .attr('y', (d: any) => d.y + 3)
      .text((d: any) => d.title.length > 22 ? `${d.title.slice(0, 22)}…` : d.title)
      .attr('font-size', 9)
      .attr('font-family', 'var(--font-sans)')
      .attr('fill', (d: any) => (d.id === focusId ? 'var(--ink-strong)' : 'var(--ink-muted)'))
      .style('pointer-events', 'none')
      .style('opacity', (d: any) => (d.id === focusId ? 0.95 : 0));

    function focus(activeId: string | null) {
      const active = activeId ? neighbours.get(activeId) : null;

      circleSel.transition('focus').duration(FADE_MS).ease(d3.easeCubicOut)
        .attr('r', (n: any) => {
          if (n.id === activeId) return baseRadius(n) + 1.5;
          return baseRadius(n);
        })
        .attr('fill', (n: any) => (n.id === activeId ? 'var(--paper)' : baseFill(n)))
        .attr('stroke', (n: any) => {
          if (n.id === activeId || n.id === focusId) return 'var(--accent)';
          return 'transparent';
        })
        .attr('opacity', (n: any) => {
          if (!active) return n.id === focusId ? 1 : 0.7;
          if (active.has(n.id)) return 1;
          return DIM;
        });

      textSel.transition('focus').duration(FADE_MS).ease(d3.easeCubicOut)
        .style('opacity', (n: any) => {
          if (active && active.has(n.id)) return n.id === activeId ? 0.95 : 0.8;
          return n.id === focusId ? 0.95 : 0;
        });

      lineSel.transition('focus').duration(FADE_MS).ease(d3.easeCubicOut)
        .attr('stroke', (l: any) => {
          if (!active) return 'var(--hairline-strong)';
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          return sId === activeId || tId === activeId ? 'var(--accent)' : 'var(--hairline-strong)';
        })
        .attr('stroke-opacity', (l: any) => {
          if (!active) return 1;
          const sId = typeof l.source === 'object' ? l.source.id : l.source;
          const tId = typeof l.target === 'object' ? l.target.id : l.target;
          return sId === activeId || tId === activeId ? 0.9 : DIM * 0.5;
        });
    }
  }, [slice, focusId, onSelect]);

  if (slice.nodes.length === 0) {
    return (
      <p className="text-xs" style={{ color: 'var(--ink-faint)' }}>
        No neighbours yet.
      </p>
    );
  }
  return <svg ref={svgRef} className="w-full h-44" role="img" aria-label="Local graph of related notes" />;
};

interface Heading {
  level: number;
  text: string;
}

function extractHeadings(content: string): Heading[] {
  const out: Heading[] = [];
  const lines = content.split('\n');
  for (const line of lines) {
    const m = line.match(/^(#{2,3})\s+(.+?)\s*$/);
    if (m) {
      const text = m[2].trim();
      if (/^update log$/i.test(text)) continue;
      out.push({ level: m[1].length, text });
    }
  }
  return out;
}
