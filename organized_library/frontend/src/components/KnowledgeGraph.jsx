import React, { useEffect, useRef, useState } from 'react';
import { Network, Maximize2, Minimize2, RotateCcw, Zap } from 'lucide-react';

const KnowledgeGraph = ({ topics, connections, selectedTopic, onTopicSelect }) => {
  const svgRef = useRef();
  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);

  // Simplified network visualization using SVG
  const renderNetwork = () => {
    if (!topics.length) return null;

    const width = isExpanded ? 800 : 400;
    const height = isExpanded ? 600 : 300;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.3;

    // Position nodes in a circle
    const nodePositions = topics.map((topic, index) => {
      const angle = (index / topics.length) * 2 * Math.PI;
      return {
        id: topic.id,
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        topic
      };
    });

    // Generate connections
    const connectionLines = connections.map(conn => {
      const fromNode = nodePositions.find(n => n.id === conn.from);
      const toNode = nodePositions.find(n => n.id === conn.to);
      
      if (!fromNode || !toNode) return null;
      
      return {
        ...conn,
        x1: fromNode.x,
        y1: fromNode.y,
        x2: toNode.x,
        y2: toNode.y
      };
    }).filter(Boolean);

    return (
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="border border-glow rounded"
        style={{ background: 'rgba(9, 19, 27, 0.8)' }}
      >
        {/* Connection Lines */}
        {connectionLines.map((conn, index) => (
          <line
            key={index}
            x1={conn.x1}
            y1={conn.y1}
            x2={conn.x2}
            y2={conn.y2}
            stroke="#08f7fe"
            strokeWidth={conn.strength * 2}
            strokeOpacity={0.3 + conn.strength * 0.4}
            className="connection-line"
          />
        ))}

        {/* Nodes */}
        {nodePositions.map((node, index) => {
          const isSelected = selectedTopic === node.id;
          const isHovered = hoveredNode === node.id;
          const nodeSize = isSelected ? 12 : isHovered ? 10 : 8;
          
          return (
            <g key={node.id}>
              {/* Node glow effect */}
              <circle
                cx={node.x}
                cy={node.y}
                r={nodeSize + 5}
                fill="none"
                stroke="#08f7fe"
                strokeWidth="1"
                strokeOpacity={isSelected || isHovered ? 0.6 : 0.2}
                className="transition-all"
              />
              
              {/* Main node */}
              <circle
                cx={node.x}
                cy={node.y}
                r={nodeSize}
                fill={isSelected ? "#08f7fe" : isHovered ? "#06d3d7" : "#048b8f"}
                stroke="#08f7fe"
                strokeWidth="2"
                className="cursor-pointer transition-all hover:filter hover:brightness-125"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onClick={() => onTopicSelect(node.id)}
              />
              
              {/* Node label */}
              {(isSelected || isHovered) && (
                <text
                  x={node.x}
                  y={node.y - nodeSize - 10}
                  textAnchor="middle"
                  fill="#08f7fe"
                  fontSize="10"
                  fontFamily="Share Tech Mono"
                  className="text-glow"
                >
                  {node.topic.title.toUpperCase()}
                </text>
              )}
            </g>
          );
        })}

        {/* Center pulse effect */}
        <circle
          cx={centerX}
          cy={centerY}
          r="3"
          fill="#08f7fe"
          className="glow-pulse"
        />
      </svg>
    );
  };

  return (
    <div className="terminal-window">
      <div className="terminal-header">
        <div className="terminal-buttons">
          <div className="terminal-button close"></div>
          <div className="terminal-button minimize"></div>
          <div className="terminal-button maximize"></div>
        </div>
        <div className="terminal-title">KNOWLEDGE GRAPH</div>
      </div>
      
      <div className="terminal-content">
        {/* Graph Controls */}
        <div className="flex items-center justify-between mb-md">
          <div className="flex items-center gap-sm">
            <Network size={16} className="text-glow" />
            <span className="text-sm text-glow">NEURAL NETWORK VISUALIZATION</span>
          </div>
          
          <div className="flex gap-xs">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="btn p-xs"
              title={isExpanded ? "Minimize" : "Expand"}
            >
              {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            </button>
            <button
              className="btn p-xs"
              title="Reset View"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>

        {/* Network Status */}
        <div className="terminal-output mb-md">
          <div className="terminal-line info">
            <span className="terminal-line-prefix">•</span>
            <span className="terminal-line-content text-sm">
              Rendering {topics.length} nodes, {connections.length} connections
            </span>
          </div>
          {selectedTopic && (
            <div className="terminal-line success">
              <span className="terminal-line-prefix">→</span>
              <span className="terminal-line-content text-sm">
                Focus: {topics.find(t => t.id === selectedTopic)?.title || 'Unknown'}
              </span>
            </div>
          )}
        </div>

        {/* Network Visualization */}
        <div className="flex justify-center mb-md">
          {renderNetwork()}
        </div>

        {/* Network Legend */}
        <div className="border-t border-muted pt-md">
          <h4 className="text-sm text-glow mb-sm">CONNECTION TYPES:</h4>
          <div className="grid grid-3 gap-sm text-xs">
            <div className="flex items-center gap-xs">
              <div className="w-4 h-px bg-glow opacity-60"></div>
              <span className="text-muted">PREREQUISITE</span>
            </div>
            <div className="flex items-center gap-xs">
              <div className="w-4 h-px bg-glow opacity-80"></div>
              <span className="text-muted">APPLICATION</span>
            </div>
            <div className="flex items-center gap-xs">
              <div className="w-4 h-px bg-glow opacity-40"></div>
              <span className="text-muted">RELATED</span>
            </div>
          </div>
        </div>

        {/* Interactive Instructions */}
        <div className="mt-md">
          <div className="terminal-output">
            <div className="terminal-line">
              <span className="terminal-line-prefix">$</span>
              <span className="terminal-line-content text-xs text-muted">
                Click nodes to explore topics • Hover for details • Use controls to navigate
              </span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        {hoveredNode && (
          <div className="mt-md p-sm border border-glow rounded fade-in">
            <div className="flex items-center gap-sm">
              <Zap size={14} className="text-glow" />
              <span className="text-sm text-glow">
                {topics.find(t => t.id === hoveredNode)?.title}
              </span>
            </div>
            <div className="text-xs text-muted mt-xs">
              {topics.find(t => t.id === hoveredNode)?.description}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeGraph;