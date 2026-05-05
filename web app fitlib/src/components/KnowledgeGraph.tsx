import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { GraphNode, GraphLink } from '../types';
import { motion } from 'motion/react';

interface KnowledgeGraphProps {
  nodes: GraphNode[];
  links: GraphLink[];
  onNodeClick: (nodeId: string) => void;
}

const SERIES_COLORS: Record<string, string> = {
  A: '#3B82F6', // Foundational
  B: '#10B981', // Resistance Training
  C: '#F59E0B', // Nutrition
  E: '#EF4444', // Cardiovascular
  Other: '#8B5CF6', // Other
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

    const link = g.append('g')
      .attr('stroke', '#94a3b8')
      .attr('stroke-opacity', 0.6)
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
      .attr('r', d => 5 + (d.credibilityScore * 15))
      .attr('fill', d => SERIES_COLORS[d.series] || SERIES_COLORS.Other)
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    node.append('title')
      .text(d => d.title);

    node.append('text')
      .attr('dy', '.35em')
      .attr('x', d => 8 + (d.credibilityScore * 15))
      .text(d => d.title)
      .style('font-size', '10px')
      .style('fill', '#e2e8f0')
      .style('pointer-events', 'none')
      .style('opacity', 0)
      .transition()
      .duration(500)
      .style('opacity', 0.8);

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
    <div ref={containerRef} className="w-full h-full bg-slate-950 overflow-hidden relative">
      <svg ref={svgRef} className="w-full h-full" />
      <div className="absolute top-4 left-4 text-slate-400 bg-slate-900/50 p-2 rounded-md backdrop-blur-sm border border-slate-800 text-xs">
        <p>A: Foundational | B: Resistance | C: Nutrition | E: Cardiovascular</p>
      </div>
    </div>
  );
};
