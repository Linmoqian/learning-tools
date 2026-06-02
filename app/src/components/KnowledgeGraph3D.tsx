import { useState, useRef, useMemo, useEffect, useCallback } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import { SUBJECT_COLORS } from '../lib/knowledge';
import type { GraphData, GraphNode, GraphEdge } from '../lib/knowledge';

// ===== 3D 力模拟 =====
interface Pos3D { x: number; y: number; z: number; vx: number; vy: number; vz: number; }

const REP = 6000;
const ATT = 0.004;
const DAMP = 0.85;
const CENTER = 0.008;
const MAX_V = 12;
const STEPS = 200;

function simulate(nodes: GraphNode[], edges: GraphEdge[], size: number): Pos3D[] {
  const p: Pos3D[] = nodes.map(() => ({
    x: (Math.random() - 0.5) * size * 0.7,
    y: (Math.random() - 0.5) * size * 0.7,
    z: (Math.random() - 0.5) * size * 0.5,
    vx: 0, vy: 0, vz: 0,
  }));

  for (let iter = 0; iter < STEPS; iter++) {
    const cool = 1 - iter / STEPS;
    for (let i = 0; i < p.length; i++) {
      for (let j = i + 1; j < p.length; j++) {
        const dx = p[j].x - p[i].x, dy = p[j].y - p[i].y, dz = p[j].z - p[i].z;
        const d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
        const f = REP / (d * d) * cool;
        const fx = dx / d * f, fy = dy / d * f, fz = dz / d * f;
        p[i].vx -= fx; p[i].vy -= fy; p[i].vz -= fz;
        p[j].vx += fx; p[j].vy += fy; p[j].vz += fz;
      }
    }
    for (const e of edges) {
      const si = nodes.findIndex(n => n.id === e.source);
      const ti = nodes.findIndex(n => n.id === e.target);
      if (si < 0 || ti < 0) continue;
      const dx = p[ti].x - p[si].x, dy = p[ti].y - p[si].y, dz = p[ti].z - p[si].z;
      const d = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
      const f = d * ATT * cool;
      p[si].vx += dx / d * f; p[si].vy += dy / d * f; p[si].vz += dz / d * f;
      p[ti].vx -= dx / d * f; p[ti].vy -= dy / d * f; p[ti].vz -= dz / d * f;
    }
    for (const q of p) {
      q.vx += -q.x * CENTER * cool; q.vy += -q.y * CENTER * cool; q.vz += -q.z * CENTER * cool;
      q.vx *= DAMP; q.vy *= DAMP; q.vz *= DAMP;
      const sp = Math.sqrt(q.vx * q.vx + q.vy * q.vy + q.vz * q.vz);
      if (sp > MAX_V) { q.vx = q.vx / sp * MAX_V; q.vy = q.vy / sp * MAX_V; q.vz = q.vz / sp * MAX_V; }
      q.x += q.vx; q.y += q.vy; q.z += q.vz;
    }
  }
  return p;
}

function connectedIds(nodeId: string, edges: GraphEdge[]): Set<string> {
  const s = new Set<string>();
  for (const e of edges) { if (e.source === nodeId) s.add(e.target); if (e.target === nodeId) s.add(e.source); }
  return s;
}

// 按连接度计算节点半径（Obsidian 风格：连接越多越大）
function calcRadius(nodeId: string, edges: GraphEdge[]): number {
  let deg = 0;
  for (const e of edges) { if (e.source === nodeId || e.target === nodeId) deg++; }
  // 2-10 之间，连接度越高半径越大
  return 3 + Math.min(deg, 12) * 0.7;
}

// ===== 连线 =====
function Edge({ from, to, highlight, dim }: { from: Pos3D; to: Pos3D; highlight: boolean; dim: boolean }) {
  const opacity = dim ? 0.02 : highlight ? 0.5 : 0.08;
  const line = useMemo(() => {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array([from.x, from.y, from.z, to.x, to.y, to.z]), 3));
    const m = new THREE.LineBasicMaterial({ color: '#a8a0b8', transparent: true, opacity, depthWrite: false });
    return new THREE.Line(g, m);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from.x, from.y, from.z, to.x, to.y, to.z, opacity]);
  return <primitive object={line} />;
}

// ===== 节点（统一为球体，Obsidian 风格） =====
const SPHERE_CACHE = new Map<number, THREE.SphereGeometry>();
function getSphere(r: number) {
  if (!SPHERE_CACHE.has(r)) SPHERE_CACHE.set(r, new THREE.SphereGeometry(r, 16, 16));
  return SPHERE_CACHE.get(r)!;
}

function NodeDot({ node, pos, color, radius, isHovered, isDimmed, onHover }: {
  node: GraphNode; pos: Pos3D; color: string; radius: number;
  isHovered: boolean; isDimmed: boolean; onHover: (id: string | null) => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      if (isHovered) {
        const s = 1 + 0.1 * Math.sin(clock.getElapsedTime() * 2.5);
        meshRef.current.scale.setScalar(s);
      } else {
        meshRef.current.scale.setScalar(1);
      }
    }
  });

  return (
    <group position={[pos.x, pos.y, pos.z]}>
      {/* 外发光环（悬停时） */}
      {isHovered && (
        <mesh>
          <sphereGeometry args={[radius * 2.5, 16, 16]} />
          <meshBasicMaterial color={color} transparent opacity={0.08} depthWrite={false} />
        </mesh>
      )}

      {/* 核心球体 */}
      <mesh
        ref={meshRef}
        geometry={getSphere(radius)}
        onPointerOver={(e) => { e.stopPropagation(); onHover(node.id); }}
        onPointerOut={() => onHover(null)}
      >
        <meshBasicMaterial
          color={color}
          transparent
          opacity={isDimmed ? 0.1 : isHovered ? 1 : 0.65}
        />
      </mesh>

      {/* 标签：仅悬停时用 Html 显示 */}
      {isHovered && (
        <Html center distanceFactor={60} position={[0, radius + 4, 0]}>
          <div style={{
            fontSize: 10,
            color: '#f0e8da',
            background: 'rgba(10,14,26,0.9)',
            padding: '2px 8px',
            borderRadius: 4,
            whiteSpace: 'nowrap',
            fontWeight: 600,
            pointerEvents: 'none',
            border: '1px solid rgba(255,255,255,0.1)',
          }}>
            {node.label}
          </div>
        </Html>
      )}
    </group>
  );
}

// ===== OrbitControls 封装（自动旋转） =====
function CameraCtrl({ active }: { active: boolean }) {
  const ref = useRef<any>(null);
  useEffect(() => {
    if (ref.current) { ref.current.autoRotate = active; ref.current.autoRotateSpeed = 0.6; }
  }, [active]);
  return <OrbitControls ref={ref} enableDamping dampingFactor={0.06} minDistance={80} maxDistance={1200} autoRotate={active} autoRotateSpeed={0.6} />;
}

// ===== 场景 =====
function Scene({ data, hoveredId, onHover }: { data: GraphData; hoveredId: string | null; onHover: (id: string | null) => void }) {
  const { size } = useThree();
  const [interacted, setInteracted] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const simSize = Math.min(size.width, size.height) * 0.4;

  const positions = useMemo(() => simulate(data.nodes, data.edges, simSize), [data, simSize]);
  const hoverConnected = hoveredId ? connectedIds(hoveredId, data.edges) : null;

  // 预计算每个节点的半径
  const radiusMap = useMemo(() => {
    const m = new Map<string, number>();
    for (const n of data.nodes) m.set(n.id, calcRadius(n.id, data.edges));
    return m;
  }, [data]);

  const onPointer = useCallback(() => {
    setInteracted(true);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setInteracted(false), 4000);
  }, []);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  return (
    <>
      <ambientLight intensity={0.8} />
      <pointLight position={[0, 0, 400]} intensity={0.3} />

      <CameraCtrl active={!interacted} />

      <group onPointerDown={onPointer} onPointerUp={onPointer}>
        {/* 连线 */}
        {positions.length > 0 && data.edges.map((e, i) => {
          const si = data.nodes.findIndex(n => n.id === e.source);
          const ti = data.nodes.findIndex(n => n.id === e.target);
          if (si < 0 || ti < 0) return null;
          const conn = hoveredId !== null && (e.source === hoveredId || e.target === hoveredId);
          const dim = hoveredId !== null && !conn;
          return <Edge key={`e${i}`} from={positions[si]} to={positions[ti]} highlight={conn} dim={dim} />;
        })}

        {/* 节点 */}
        {positions.length > 0 && data.nodes.map((n, i) => {
          const p = positions[i]; if (!p) return null;
          const isHov = hoveredId === n.id;
          const isDim = hoveredId !== null && n.id !== hoveredId && !(hoverConnected?.has(n.id));
          const color = SUBJECT_COLORS[n.subject] || '#666';
          return (
            <NodeDot
              key={n.id} node={n} pos={p} color={color}
              radius={radiusMap.get(n.id) || 4}
              isHovered={isHov} isDimmed={isDim} onHover={onHover}
            />
          );
        })}
      </group>
    </>
  );
}

// ===== 主组件 =====
interface Props { data: GraphData; }

export default function KnowledgeGraph3D({ data }: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div style={{
      width: '100%', height: '100%', minHeight: 400,
      position: 'relative', borderRadius: 16, overflow: 'hidden',
    }}>
      {/* 悬停节点提示 */}
      <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 10 }}>
        <span style={{ fontSize: 10, color: '#6b6480' }}>
          悬停查看连接 · 拖拽旋转 · 滚轮缩放
        </span>
      </div>

      {!data.nodes.length && (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#6b6480', fontSize: 14 }}>
          暂无数据
        </div>
      )}

      {data.nodes.length > 0 && (
        <Canvas
          camera={{ position: [80, 60, 250], fov: 45 }}
          dpr={[1, 2]}
          style={{ background: 'radial-gradient(ellipse at center, #111827 0%, #0a0e1a 100%)' }}
        >
          <Scene data={data} hoveredId={hoveredId} onHover={setHoveredId} />
        </Canvas>
      )}

      {/* 图例（底部） */}
      <div style={{
        position: 'absolute', bottom: 12, left: '50%', transform: 'translateX(-50%)',
        display: 'flex', gap: 16, alignItems: 'center',
        background: 'rgba(10,14,26,0.8)', padding: '5px 14px', borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.06)', backdropFilter: 'blur(8px)',
      }}>
        {Object.entries(SUBJECT_COLORS).map(([s, c]) => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: c, boxShadow: `0 0 4px ${c}66` }} />
            <span style={{ fontSize: 9, color: '#6b6480' }}>{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
