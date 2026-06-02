import { useState, useRef, useEffect, useCallback } from 'react';
import { SUBJECT_COLORS } from '../lib/knowledge';
import type { GraphData, GraphNode, GraphEdge } from '../lib/knowledge';

interface Position { x: number; y: number; vx: number; vy: number; }

interface Props {
  data: GraphData;
  width?: number;
  height?: number;
}

const REPULSION = 6000;
const ATTRACTION = 0.005;
const DAMPING = 0.85;
const CENTER_STRENGTH = 0.01;
const MAX_SPEED = 8;

function simulateForceDirected(nodes: GraphNode[], edges: GraphEdge[], w: number, h: number): Position[] {
  const pos: Position[] = nodes.map(() => ({
    x: (Math.random() - 0.5) * w * 0.6,
    y: (Math.random() - 0.5) * h * 0.6,
    vx: 0,
    vy: 0,
  }));

  for (let iter = 0; iter < 120; iter++) {
    const cooling = 1 - iter / 120;

    // Repulsion between all pairs
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        let dx = pos[j].x - pos[i].x;
        let dy = pos[j].y - pos[i].y;
        let dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = REPULSION / (dist * dist);
        const fx = (dx / dist) * force * cooling;
        const fy = (dy / dist) * force * cooling;
        pos[i].vx -= fx;
        pos[i].vy -= fy;
        pos[j].vx += fx;
        pos[j].vy += fy;
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const si = nodes.findIndex(n => n.id === edge.source);
      const ti = nodes.findIndex(n => n.id === edge.target);
      if (si < 0 || ti < 0) continue;
      const dx = pos[ti].x - pos[si].x;
      const dy = pos[ti].y - pos[si].y;
      const dist = Math.sqrt(dx * dx + dy * dy) || 1;
      const force = dist * ATTRACTION * cooling;
      pos[si].vx += (dx / dist) * force;
      pos[si].vy += (dy / dist) * force;
      pos[ti].vx -= (dx / dist) * force;
      pos[ti].vy -= (dy / dist) * force;
    }

    // Center gravity
    for (const p of pos) {
      p.vx += (-p.x) * CENTER_STRENGTH * cooling;
      p.vy += (-p.y) * CENTER_STRENGTH * cooling;
    }

    // Apply velocity with damping
    for (const p of pos) {
      p.vx *= DAMPING;
      p.vy *= DAMPING;
      const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
      if (speed > MAX_SPEED) {
        p.vx = (p.vx / speed) * MAX_SPEED;
        p.vy = (p.vy / speed) * MAX_SPEED;
      }
      p.x += p.vx;
      p.y += p.vy;
    }
  }

  return pos;
}

export default function KnowledgeGraph({ data, width: propW, height: propH }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dim, setDim] = useState({ w: propW || 640, h: propH || 480 });
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [showLabels, setShowLabels] = useState(false);

  useEffect(() => {
    if (!propW && containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      setDim({ w: rect.width, h: rect.height || 480 });
    }
  }, [propW]);

  useEffect(() => {
    if (data.nodes.length) {
      setPositions(simulateForceDirected(data.nodes, data.edges, dim.w * 0.8, dim.h * 0.8));
    }
  }, [data, dim]);

  const cx = dim.w / 2;
  const cy = dim.h / 2;

  const getConnectedEdges = useCallback((nodeId: string): string[] => {
    const connected = new Set<string>();
    for (const edge of data.edges) {
      if (edge.source === nodeId) connected.add(edge.target);
      if (edge.target === nodeId) connected.add(edge.source);
    }
    return [...connected];
  }, [data.edges]);

  const isConnected = useCallback((nodeId: string, connectedIds: Set<string>): boolean => {
    return connectedIds.has(nodeId);
  }, []);

  const edgeOpacity = (edge: GraphEdge, connectedIds: Set<string> | null) => {
    if (!connectedIds) return 0.08;
    return (connectedIds.has(edge.source) || connectedIds.has(edge.target)) ? 0.4 : 0.04;
  };

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: propH || '100%',
        minHeight: 400,
        position: 'relative',
        borderRadius: 16,
        overflow: 'hidden',
        background: 'rgba(15,20,34,0.5)',
        border: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      {/* Controls */}
      <div style={{ position: 'absolute', top: 12, right: 12, zIndex: 10, display: 'flex', gap: 8 }}>
        <button
          onClick={() => setShowLabels(!showLabels)}
          style={{
            padding: '4px 12px',
            borderRadius: 6,
            border: '1px solid rgba(255,255,255,0.12)',
            background: 'rgba(15,20,34,0.8)',
            color: showLabels ? '#f0c040' : '#a8a0b8',
            fontSize: 11,
            cursor: 'pointer',
            transition: 'all 0.15s',
          }}
        >
          {showLabels ? '隐藏标签' : '显示标签'}
        </button>
      </div>

      {/* Empty state */}
      {!data.nodes.length && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          height: '100%', color: '#6b6480', fontSize: 14,
        }}>
          暂无数据
        </div>
      )}

      {/* SVG Graph */}
      {data.nodes.length > 0 && (
        <svg width={dim.w} height={dim.h} style={{ display: 'block' }}>
          {/* Edges */}
          {positions.length > 0 && data.edges.map((edge, i) => {
            const si = data.nodes.findIndex(n => n.id === edge.source);
            const ti = data.nodes.findIndex(n => n.id === edge.target);
            if (si < 0 || ti < 0) return null;
            const p1 = positions[si];
            const p2 = positions[ti];
            const connectedIds = hoveredNode
              ? new Set(getConnectedEdges(hoveredNode))
              : null;

            return (
              <line
                key={`edge-${i}`}
                x1={cx + p1.x}
                y1={cy + p1.y}
                x2={cx + p2.x}
                y2={cy + p2.y}
                stroke="#f0c040"
                strokeWidth={1}
                opacity={edgeOpacity(edge, connectedIds)}
              />
            );
          })}

          {/* Nodes */}
          {positions.length > 0 && data.nodes.map((node, i) => {
            const pos = positions[i];
            if (!pos) return null;
            const x = cx + pos.x;
            const y = cy + pos.y;
            const color = SUBJECT_COLORS[node.subject] || '#666';
            const isHovered = hoveredNode === node.id;
            const connectedIds = hoveredNode ? new Set(getConnectedEdges(hoveredNode)) : null;
            const isDimmed = hoveredNode && node.id !== hoveredNode && !isConnected(node.id, connectedIds!);

            return (
              <g key={node.id}>
                {/* Glow */}
                {isHovered && (
                  <circle
                    cx={x}
                    cy={y}
                    r={node.radius + 8}
                    fill="none"
                    stroke={color}
                    strokeWidth={2}
                    opacity={0.3}
                  >
                    <animate attributeName="r" from={node.radius + 4} to={node.radius + 12} dur="1.5s" repeatCount="indefinite" />
                    <animate attributeName="opacity" from="0.4" to="0.1" dur="1.5s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Shape */}
                {node.type === 'note' ? (
                  <rect
                    x={x - node.radius}
                    y={y - node.radius}
                    width={node.radius * 2}
                    height={node.radius * 2}
                    rx={4}
                    fill={color}
                    opacity={isDimmed ? 0.2 : 0.9}
                    stroke={isHovered ? '#f0c040' : 'rgba(255,255,255,0.15)'}
                    strokeWidth={isHovered ? 2 : 1}
                    style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                  />
                ) : (
                  <circle
                    cx={x}
                    cy={y}
                    r={node.radius}
                    fill={color}
                    opacity={isDimmed ? 0.2 : 0.85}
                    stroke={isHovered ? '#f0c040' : 'rgba(255,255,255,0.15)'}
                    strokeWidth={isHovered ? 2 : 1}
                    style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                  />
                )}

                {/* Label */}
                {showLabels && (
                  <text
                    x={x}
                    y={y + (node.type === 'note' ? 0 : 4)}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill={isDimmed ? 'rgba(160,160,180,0.3)' : '#f0e8da'}
                    fontSize={node.type === 'note' ? 9 : 8}
                    fontWeight={600}
                    opacity={isDimmed ? 0.3 : 1}
                    style={{ pointerEvents: 'none' }}
                  >
                    {node.label}
                  </text>
                )}

                {/* Type indicator for notes */}
                {node.type === 'note' && !showLabels && isHovered && (
                  <text
                    x={x}
                    y={y + node.radius + 14}
                    textAnchor="middle"
                    fill="#f0e8da"
                    fontSize={9}
                    fontWeight={600}
                    style={{ pointerEvents: 'none' }}
                  >
                    {node.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      )}

      {/* Legend */}
      <div style={{
        position: 'absolute', bottom: 12, left: 12,
        display: 'flex', gap: 12, flexWrap: 'wrap',
        background: 'rgba(15,20,34,0.8)',
        padding: '6px 12px',
        borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        {Object.entries(SUBJECT_COLORS).map(([subject, color]) => (
          <div key={subject} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: 2, background: color }} />
            <span style={{ fontSize: 10, color: '#a8a0b8' }}>{subject}</span>
          </div>
        ))}
      </div>

      {/* Type legend */}
      <div style={{
        position: 'absolute', bottom: 12, right: 12,
        display: 'flex', gap: 12,
        background: 'rgba(15,20,34,0.8)',
        padding: '6px 12px',
        borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.06)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#a8a0b8' }} />
          <span style={{ fontSize: 10, color: '#a8a0b8' }}>笔记</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#a8a0b8' }} />
          <span style={{ fontSize: 10, color: '#a8a0b8' }}>知识点</span>
        </div>
      </div>
    </div>
  );
}
