import { useState, useRef, useMemo, useCallback, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import { SUBJECT_COLORS } from '../lib/knowledge';
import type { GraphData, GraphNode, GraphEdge } from '../lib/knowledge';

// === 3D Force Simulation ===
interface Position3D {
  x: number; y: number; z: number;
  vx: number; vy: number; vz: number;
}

const REPULSION = 8000;
const ATTRACTION = 0.005;
const DAMPING = 0.85;
const CENTER_STRENGTH = 0.01;
const MAX_SPEED = 10;
const ITERATIONS = 180;

function simulate3D(nodes: GraphNode[], edges: GraphEdge[], size: number): Position3D[] {
  const pos: Position3D[] = nodes.map(() => ({
    x: (Math.random() - 0.5) * size * 0.8,
    y: (Math.random() - 0.5) * size * 0.8,
    z: (Math.random() - 0.5) * size * 0.6,
    vx: 0, vy: 0, vz: 0,
  }));

  for (let iter = 0; iter < ITERATIONS; iter++) {
    const cooling = 1 - iter / ITERATIONS;

    // Repulsion between all pairs (3D)
    for (let i = 0; i < pos.length; i++) {
      for (let j = i + 1; j < pos.length; j++) {
        const dx = pos[j].x - pos[i].x;
        const dy = pos[j].y - pos[i].y;
        const dz = pos[j].z - pos[i].z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
        const force = REPULSION / (dist * dist) * cooling;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;
        const fz = (dz / dist) * force;
        pos[i].vx -= fx; pos[i].vy -= fy; pos[i].vz -= fz;
        pos[j].vx += fx; pos[j].vy += fy; pos[j].vz += fz;
      }
    }

    // Attraction along edges
    for (const edge of edges) {
      const si = nodes.findIndex(n => n.id === edge.source);
      const ti = nodes.findIndex(n => n.id === edge.target);
      if (si < 0 || ti < 0) continue;
      const dx = pos[ti].x - pos[si].x;
      const dy = pos[ti].y - pos[si].y;
      const dz = pos[ti].z - pos[si].z;
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
      const force = dist * ATTRACTION * cooling;
      pos[si].vx += (dx / dist) * force;
      pos[si].vy += (dy / dist) * force;
      pos[si].vz += (dz / dist) * force;
      pos[ti].vx -= (dx / dist) * force;
      pos[ti].vy -= (dy / dist) * force;
      pos[ti].vz -= (dz / dist) * force;
    }

    // Center gravity (keep nodes loosely centered)
    for (const p of pos) {
      p.vx += (-p.x) * CENTER_STRENGTH * cooling;
      p.vy += (-p.y) * CENTER_STRENGTH * cooling;
      p.vz += (-p.z) * CENTER_STRENGTH * cooling;
    }

    // Damping + velocity
    for (const p of pos) {
      p.vx *= DAMPING;
      p.vy *= DAMPING;
      p.vz *= DAMPING;
      const speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy + p.vz * p.vz);
      if (speed > MAX_SPEED) {
        p.vx = (p.vx / speed) * MAX_SPEED;
        p.vy = (p.vy / speed) * MAX_SPEED;
        p.vz = (p.vz / speed) * MAX_SPEED;
      }
      p.x += p.vx;
      p.y += p.vy;
      p.z += p.vz;
    }
  }

  return pos;
}

// === Helpers ===
function getConnectedNodeIds(nodeId: string, edges: GraphEdge[]): Set<string> {
  const ids = new Set<string>();
  for (const edge of edges) {
    if (edge.source === nodeId) ids.add(edge.target);
    if (edge.target === nodeId) ids.add(edge.source);
  }
  return ids;
}

// === Edge Line (using THREE.Line via primitive) ===
function EdgeLine({ from, to, highlight, dim }: {
  from: Position3D; to: Position3D;
  highlight: boolean; dim: boolean;
}) {
  const opacity = dim ? 0.03 : highlight ? 0.45 : 0.1;

  const line = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const vertices = new Float32Array([
      from.x, from.y, from.z,
      to.x, to.y, to.z,
    ]);
    geo.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    const mat = new THREE.LineBasicMaterial({
      color: '#f0c040',
      transparent: true,
      opacity,
    });
    return new THREE.Line(geo, mat);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [from.x, from.y, from.z, to.x, to.y, to.z, opacity]);

  return <primitive object={line} />;
}

// === Pulsing glow ring ===
function GlowRing({ color }: { color: string }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      const t = clock.getElapsedTime();
      const s = 1 + 0.15 * Math.sin(t * 2);
      meshRef.current.scale.setScalar(s);
      (meshRef.current.material as THREE.MeshBasicMaterial).opacity = 0.15 + 0.1 * Math.sin(t * 2);
    }
  });

  return (
    <mesh ref={meshRef}>
      <sphereGeometry args={[10, 16, 16]} />
      <meshBasicMaterial color={color} transparent opacity={0.15} depthWrite={false} />
    </mesh>
  );
}

// === Shared geometries (prevent re-creation on each render) ===
const SPHERE_GEO = new THREE.SphereGeometry(7, 20, 20);
const BOX_GEO = new THREE.BoxGeometry(12, 12, 12);

// === Node Mesh ===
function NodeMesh({ node, position, color, isHovered, isDimmed, showLabel, onHover }: {
  node: GraphNode;
  position: Position3D;
  color: string;
  isHovered: boolean;
  isDimmed: boolean;
  showLabel: boolean;
  onHover: (id: string | null) => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      if (isHovered) {
        const s = 1 + 0.05 * Math.sin(clock.getElapsedTime() * 3);
        meshRef.current.scale.setScalar(s);
      } else {
        meshRef.current.scale.setScalar(1);
      }
    }
  });

  const geometry = node.type === 'note' ? BOX_GEO : SPHERE_GEO;
  const labelY = node.type === 'note' ? -10 : -8;

  return (
    <group position={[position.x, position.y, position.z]}>
      {/* Glow ring on hover */}
      {isHovered && <GlowRing color={color} />}

      {/* Main mesh */}
      <mesh
        ref={meshRef}
        geometry={geometry}
        onPointerOver={(e) => { e.stopPropagation(); onHover(node.id); }}
        onPointerOut={() => onHover(null)}
      >
        <meshStandardMaterial
          color={color}
          roughness={0.3}
          metalness={0.1}
          transparent
          opacity={isDimmed ? 0.2 : 0.9}
          emissive={isHovered ? color : '#000'}
          emissiveIntensity={isHovered ? 0.4 : 0}
        />
      </mesh>

      {/* HTML label — always faces camera via Html billboard */}
      {(showLabel || isHovered) && (
        <Html center distanceFactor={50} position={[0, labelY, 0]}>
          <div style={{
            fontSize: 10,
            color: '#f0e8da',
            background: 'rgba(10,14,26,0.85)',
            padding: '2px 6px',
            borderRadius: 4,
            whiteSpace: 'nowrap',
            fontWeight: 600,
            pointerEvents: 'none',
            border: '1px solid rgba(255,255,255,0.08)',
            opacity: isDimmed ? 0.3 : 1,
          }}>
            {node.label}
          </div>
        </Html>
      )}
    </group>
  );
}

// === Camera Auto-Rotate Controller ===
function CameraController({ autoRotate }: { autoRotate: boolean }) {
  const controlsRef = useRef<any>(null);

  useEffect(() => {
    if (controlsRef.current) {
      controlsRef.current.autoRotate = autoRotate;
      controlsRef.current.autoRotateSpeed = 0.8;
    }
  }, [autoRotate]);

  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping
      dampingFactor={0.08}
      minDistance={100}
      maxDistance={1500}
      autoRotate={autoRotate}
      autoRotateSpeed={0.8}
    />
  );
}

// === Scene ===
function GraphScene({ data, showLabels, hoveredId, onHover }: {
  data: GraphData;
  showLabels: boolean;
  hoveredId: string | null;
  onHover: (id: string | null) => void;
}) {
  const { size } = useThree();
  const [userInteracted, setUserInteracted] = useState(false);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Re-simulate when data or viewport size changes
  const simSize = Math.min(size.width, size.height) * 0.45;
  const positions = useMemo(
    () => simulate3D(data.nodes, data.edges, simSize),
    [data, simSize],
  );

  const connectedIds = hoveredId ? getConnectedNodeIds(hoveredId, data.edges) : null;

  // Reset auto-rotate idle timer on user interaction
  const handleStart = useCallback(() => {
    setUserInteracted(true);
    if (idleTimer.current) clearTimeout(idleTimer.current);
    idleTimer.current = setTimeout(() => setUserInteracted(false), 3000);
  }, []);

  useEffect(() => {
    return () => {
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, []);

  return (
    <>
      {/* Ambient + directional lights for 3D depth */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[200, 300, 200]} intensity={1.0} />
      <directionalLight position={[-200, -100, -200]} intensity={0.3} />
      <pointLight position={[0, 0, 300]} intensity={0.2} />

      <CameraController autoRotate={!userInteracted} />

      {/* Interaction tracking group */}
      <group onPointerDown={handleStart} onPointerUp={handleStart}>
        {/* Edges */}
        {positions.length > 0 && data.edges.map((edge, i) => {
          const si = data.nodes.findIndex(n => n.id === edge.source);
          const ti = data.nodes.findIndex(n => n.id === edge.target);
          if (si < 0 || ti < 0) return null;
          const isConnected = hoveredId !== null
            && (edge.source === hoveredId || edge.target === hoveredId);
          const isDimmed = hoveredId !== null && !isConnected;
          return (
            <EdgeLine
              key={`edge-${i}`}
              from={positions[si]}
              to={positions[ti]}
              highlight={isConnected}
              dim={isDimmed}
            />
          );
        })}

        {/* Nodes */}
        {positions.length > 0 && data.nodes.map((node, i) => {
          const pos = positions[i];
          if (!pos) return null;
          const isHovered = hoveredId === node.id;
          const isDimmed = hoveredId !== null
            && node.id !== hoveredId
            && !(connectedIds?.has(node.id));
          const color = SUBJECT_COLORS[node.subject] || '#666';

          return (
            <NodeMesh
              key={node.id}
              node={node}
              position={pos}
              color={color}
              isHovered={isHovered}
              isDimmed={isDimmed}
              showLabel={showLabels}
              onHover={onHover}
            />
          );
        })}
      </group>
    </>
  );
}

// === Main Exported Component ===
interface Props {
  data: GraphData;
}

export default function KnowledgeGraph3D({ data }: Props) {
  const [showLabels, setShowLabels] = useState(false);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      minHeight: 400,
      position: 'relative',
      borderRadius: 16,
      overflow: 'hidden',
    }}>
      {/* Controls overlay */}
      <div style={{
        position: 'absolute', top: 12, right: 12, zIndex: 10,
        display: 'flex', gap: 8, alignItems: 'center',
      }}>
        {/* Hovered node info */}
        {hoveredId && (
          <span style={{
            fontSize: 11, color: '#f0e8da',
            background: 'rgba(10,14,26,0.85)',
            padding: '4px 10px', borderRadius: 6,
          }}>
            {data.nodes.find(n => n.id === hoveredId)?.label}
          </span>
        )}
        <button
          onClick={() => setShowLabels(!showLabels)}
          style={{
            padding: '5px 14px', borderRadius: 6,
            border: '1px solid rgba(255,255,255,0.12)',
            background: 'rgba(10,14,26,0.85)',
            color: showLabels ? '#f0c040' : '#a8a0b8',
            fontSize: 11, cursor: 'pointer',
            fontWeight: 600,
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

      {/* Three.js Canvas */}
      {data.nodes.length > 0 && (
        <Canvas
          camera={{ position: [100, 80, 300], fov: 50 }}
          dpr={[1, 2]}
          style={{ background: 'radial-gradient(ellipse at center, #111827 0%, #0a0e1a 100%)' }}
        >
          <GraphScene
            data={data}
            showLabels={showLabels}
            hoveredId={hoveredId}
            onHover={setHoveredId}
          />
        </Canvas>
      )}

      {/* Subject legend */}
      <div style={{
        position: 'absolute', bottom: 12, left: 12,
        display: 'flex', gap: 12, flexWrap: 'wrap',
        background: 'rgba(10,14,26,0.85)',
        padding: '6px 12px', borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(8px)',
      }}>
        {Object.entries(SUBJECT_COLORS).map(([subject, color]) => (
          <div key={subject} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{
              width: 8, height: 8, borderRadius: 2,
              background: color,
              boxShadow: `0 0 6px ${color}66`,
            }} />
            <span style={{ fontSize: 10, color: '#a8a0b8' }}>{subject}</span>
          </div>
        ))}
      </div>

      {/* Type legend */}
      <div style={{
        position: 'absolute', bottom: 12, right: 12,
        display: 'flex', gap: 12,
        background: 'rgba(10,14,26,0.85)',
        padding: '6px 12px', borderRadius: 8,
        border: '1px solid rgba(255,255,255,0.06)',
        backdropFilter: 'blur(8px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: 10, height: 10, borderRadius: 2,
            background: 'rgba(168,160,184,0.6)',
          }} />
          <span style={{ fontSize: 10, color: '#a8a0b8' }}>笔记</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: 'rgba(168,160,184,0.6)',
          }} />
          <span style={{ fontSize: 10, color: '#a8a0b8' }}>知识点</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <div style={{
            width: 12, height: 2,
            background: 'rgba(240,192,64,0.5)',
            borderRadius: 1,
          }} />
          <span style={{ fontSize: 10, color: '#a8a0b8' }}>引用</span>
        </div>
      </div>
    </div>
  );
}
