import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GraphNode, GraphLink } from '../types';

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onNodeClick: (nodeId: string) => void;
}

// Resolved off the live theme tokens at render time so dark/light flips
// are picked up automatically. The `series` palette deliberately sits in
// muted tones — the graph is reference, not poster art.
const SERIES_COLORS: Record<string, string> = {
  A: '#7DB7FF',
  B: '#7BC9A2',
  C: '#E0B179',
  D: '#B8A4DA',
  E: '#E07B7B',
  F: '#E6C77A',
  Other: '#8E94A0',
};

export const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ nodes, links, onNodeClick }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const g = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links).id(d => d.id).distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(d => (d as GraphNode).credibilityScore * 15 + 10));

    const styles = getComputedStyle(document.documentElement);
    const inkFaint = styles.getPropertyValue('--ink-faint').trim() || '#6A707A';
    const inkMuted = styles.getPropertyValue('--ink-muted').trim() || '#A0A4AC';
    const inkStrong = styles.getPropertyValue('--ink-strong').trim() || '#FFFFFF';
    const paper = styles.getPropertyValue('--paper').trim() || '#0F1115';

    const link = g.append('g')
      .attr('stroke', inkFaint)
      .attr('stroke-opacity', 0.45)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', d => Math.sqrt(d.strength || 1));

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => onNodeClick(d.id))
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended));

    node.append('circle')
      .attr('r', d => 4 + (d.credibilityScore * 12))
      .attr('fill', d => SERIES_COLORS[d.series] || SERIES_COLORS.Other)
      .attr('stroke', paper)
      .attr('stroke-width', 1.5);

    node.append('title').text(d => d.title);

    node.append('text')
      .attr('dy', '.35em')
      .attr('x', d => 8 + (d.credibilityScore * 12))
      .text(d => d.title)
      .style('font-size', '10px')
      .style('font-family', 'var(--font-sans), sans-serif')
      .style('fill', inkMuted)
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .transition()
      .duration(500)
      .style('opacity', 0.85);

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return () => {
      simulation.stop();
    };
  }, [nodes, links, onNodeClick]);

  return (
    <div
      ref={containerRef}
      className="w-full h-full overflow-hidden relative"
      style={{ background: 'var(--paper)' }}
    >
      <svg ref={svgRef} className="w-full h-full" />
      <div
        className="absolute top-4 left-4 px-3 py-2 rounded-lg flex items-center gap-3 flex-wrap"
        style={{
          background: 'var(--paper-raised)',
          border: '1px solid var(--hairline)',
        }}
      >
        {Object.entries(SERIES_COLORS).map(([key, colour]) => (
          <span
            key={key}
            className="inline-flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-widest"
            style={{ color: 'var(--ink-muted)' }}
          >
            <span
              className="w-1.5 h-1.5 rounded-full"
              style={{ background: colour }}
            />
            {key}
          </span>
        ))}
      </div>
    </div>
  );
};
