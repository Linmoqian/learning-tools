import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { Sparkles, ListOrdered, Timer as TimerIcon, Star } from 'lucide-react';
import ChoiceDialog from '../components/ChoiceDialog';
import ReplaceDialog from '../components/ReplaceDialog';
import Timer from '../components/Timer';
import StatusBar from '../components/StatusBar';
import { useStore } from '../lib/store';
import {
  Task, GachaSessionContext, DrawChoiceResult,
  GACHA_POOL_NAMES, GACHA_POOL_RANGES, GachaPool,
} from '../lib/types';
import {
  getPoolForTime, filterByPool, getTopWeighted, planMultiDraw,
  createSessionContext, isDdlUrgent,
} from '../lib/algorithms';

// ====================================================================
// 美学常量
// ====================================================================

const COSMIC = {
  void: '#050510',
  deepNebula: '#0c0824',
  midNebula: '#1a0a2e',
  gold: '#d4a843',
  goldLight: '#f0d878',
  goldDark: '#a07d2e',
  purple: '#7c3aed',
  purpleLight: '#a78bfa',
  blue: '#0ea5e9',
  ember: '#f97316',
  starWhite: '#f0f4ff',
  textPrimary: '#f0e8da',
  textSecondary: '#a8a0b8',
  textMuted: '#6b6480',
  glassBg: 'rgba(10, 5, 32, 0.6)',
  glassBorder: 'rgba(212, 168, 67, 0.12)',
};

const POOL_CONFIG: Record<string, { gradient: string; glow: string; icon: string; desc: string; aura: string }> = {
  [GachaPool.FRAGMENT]: {
    gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    glow: 'rgba(99,102,241,0.5)',
    icon: '✦',
    desc: '碎片时隙',
    aura: 'rgba(99,102,241,0.08)',
  },
  [GachaPool.TOMATO]: {
    gradient: 'linear-gradient(135deg, #d4a843, #f97316)',
    glow: 'rgba(212,168,67,0.5)',
    icon: '☀',
    desc: '专注时隙',
    aura: 'rgba(212,168,67,0.08)',
  },
  [GachaPool.DEEP]: {
    gradient: 'linear-gradient(135deg, #ef4444, #ec4899)',
    glow: 'rgba(239,68,68,0.5)',
    icon: '🔥',
    desc: '深度时隙',
    aura: 'rgba(239,68,68,0.08)',
  },
};

const RARITY = [
  { stars: 5, label: '传说', gradient: 'linear-gradient(135deg, #d4a843, #f97316)', glow: 'rgba(212,168,67,0.35)', bg: 'rgba(212,168,67,0.08)' },
  { stars: 4, label: '史诗', gradient: 'linear-gradient(135deg, #7c3aed, #ec4899)', glow: 'rgba(124,58,237,0.35)', bg: 'rgba(124,58,237,0.08)' },
  { stars: 3, label: '稀有', gradient: 'linear-gradient(135deg, #0ea5e9, #06b6d4)', glow: 'rgba(14,165,233,0.35)', bg: 'rgba(14,165,233,0.08)' },
  { stars: 2, label: '普通', gradient: 'linear-gradient(135deg, #6b7280, #9ca3af)', glow: 'rgba(107,114,128,0.3)', bg: 'rgba(107,114,128,0.06)' },
];

function getTaskRarity(task: Task) {
  if (isDdlUrgent(task)) return RARITY[0];
  if (task.priority >= 4) return RARITY[1];
  if (task.priority >= 2) return RARITY[2];
  return RARITY[3];
}

// ====================================================================
// 字体加载
// ====================================================================
function useFontLoader() {
  useEffect(() => {
    if (document.querySelector('[data-cosmic-fonts]')) return;
    const link = document.createElement('link');
    link.setAttribute('data-cosmic-fonts', '');
    link.rel = 'stylesheet';
    link.href = 'https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Cinzel:wght@400;500;600;700&family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap';
    document.head.appendChild(link);
  }, []);
}

// ====================================================================
// 流星系统 (GSAP)
// ====================================================================
function ShootingStars({ intensity = 1 }: { intensity?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const meteors: gsap.core.Tween[] = [];
    let interval: number;

    const spawn = () => {
      const meteor = document.createElement('div');
      const head = document.createElement('div');
      const trail = document.createElement('div');

      const length = 100 + Math.random() * 150;
      const angle = -20 + Math.random() * -25; // -20 ~ -45 degrees
      const rad = (angle * Math.PI) / 180;
      const startX = window.innerWidth * 0.3 + Math.random() * window.innerWidth * 0.7;
      const startY = -40 - Math.random() * 120;
      const distance = 500 + Math.random() * 500;

      trail.style.cssText = `
        position: absolute; left: 0; top: 0;
        width: ${length}px; height: 2px;
        background: linear-gradient(to left, transparent 0%, rgba(212,168,67,0.6) 40%, rgba(255,240,200,1) 70%, #fff 100%);
        border-radius: 1px 0 0 1px;
        filter: blur(0.5px);
        pointer-events: none;
      `;
      head.style.cssText = `
        position: absolute;
        right: -3px; top: -2px;
        width: 5px; height: 5px;
        background: radial-gradient(circle, #fff 20%, rgba(255,240,200,0.8) 60%, transparent);
        border-radius: 50%;
        filter: blur(0.5px);
        pointer-events: none;
      `;
      meteor.appendChild(trail);
      meteor.appendChild(head);
      meteor.style.cssText = `
        position: absolute; left: 0; top: 0;
        transform: rotate(${angle}deg);
        transform-origin: right center;
        pointer-events: none;
        z-index: 2;
      `;
      container.appendChild(meteor);

      const endX = startX + Math.cos(rad) * distance;
      const endY = startY + Math.sin(rad) * distance;
      const duration = 0.6 + Math.random() * 0.5;

      const tween = gsap.fromTo(meteor,
        { x: startX, y: startY, opacity: 1 },
        {
          x: endX, y: endY, opacity: 0,
          duration,
          ease: 'power2.out',
          onComplete: () => { meteor.remove(); },
        },
      );
      meteors.push(tween);

      // Glow trail 残留
      const glow = document.createElement('div');
      glow.style.cssText = `
        position: absolute; left: ${startX + length}px; top: ${startY}px;
        width: 3px; height: 3px;
        background: rgba(212,168,67,0.4);
        border-radius: 50%;
        filter: blur(3px);
        pointer-events: none; z-index: 1;
      `;
      container.appendChild(glow);
      gsap.to(glow, { opacity: 0, scale: 0, duration: 2, delay: 0.1, onComplete: () => glow.remove() });
    };

    const baseInterval = Math.max(800, 3000 / intensity);
    const initialBatch = Math.min(3, Math.round(2 * intensity));
    for (let i = 0; i < initialBatch; i++) {
      setTimeout(spawn, i * (300 + Math.random() * 400));
    }
    interval = window.setInterval(() => {
      if (document.hidden) return;
      spawn();
      if (Math.random() > 0.55) setTimeout(spawn, 150 + Math.random() * 200);
    }, baseInterval + Math.random() * 1500);

    return () => {
      clearInterval(interval);
      meteors.forEach(t => t.kill());
      container.innerHTML = '';
    };
  }, [intensity]);

  return <div ref={containerRef} style={{ position: 'fixed', inset: 0, overflow: 'hidden', zIndex: 2, pointerEvents: 'none' }} />;
}

// ====================================================================
// 星座星图 (SVG)
// ====================================================================
function ConstellationField() {
  const stars = useMemo(() => {
    const pts = Array.from({ length: 50 }, (_, i) => ({
      id: i, x: Math.random() * 100, y: Math.random() * 100,
      size: 0.5 + Math.random() * 2.5, bright: Math.random(),
      delay: Math.random() * 5, pulse: 2 + Math.random() * 4,
    }));

    const lines: Array<[number, number]> = [];
    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const dx = pts[i].x - pts[j].x;
        const dy = pts[i].y - pts[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 15 && Math.random() > 0.7) {
          lines.push([i, j]);
        }
      }
    }
    return { points: pts, lines };
  }, []);

  return (
    <svg style={{ position: 'fixed', inset: 0, width: '100%', height: '100%', zIndex: 1, pointerEvents: 'none' }}>
      {/* Constellation lines */}
      {stars.lines.map(([a, b], i) => {
        const p1 = stars.points[a];
        const p2 = stars.points[b];
        return (
          <line
            key={`l-${i}`}
            x1={`${p1.x}%`} y1={`${p1.y}%`}
            x2={`${p2.x}%`} y2={`${p2.y}%`}
            stroke="rgba(212,168,67,0.08)"
            strokeWidth="0.5"
            strokeDasharray="4 3"
            style={{ animation: `constellation-draw 3s ${Math.random() * 5}s ease-out` }}
          />
        );
      })}
      {/* Stars */}
      {stars.points.map(s => (
        <g key={s.id}>
          <circle
            cx={`${s.x}%`} cy={`${s.y}%`} r={s.size * 0.6}
            fill={s.bright > 0.7 ? 'var(--gold-light)' : '#64748b'}
            opacity={0.15 + s.size * 0.12}
            style={{ animation: s.bright > 0.7 ? `pulse-star ${s.pulse}s ${s.delay}s ease-in-out infinite` : 'none' }}
          />
          {s.size > 1.5 && (
            <circle
              cx={`${s.x}%`} cy={`${s.y}%`} r={s.size * 0.15}
              fill="#fff" opacity={0.3}
              style={{ animation: `pulse-star ${s.pulse * 0.7}s ${s.delay}s ease-in-out infinite` }}
            />
          )}
        </g>
      ))}
    </svg>
  );
}

// ====================================================================
// 星云背景
// ====================================================================
function NebulaBackground() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
      {/* Base */}
      <div style={{ position: 'absolute', inset: 0, background: COSMIC.void }} />
      {/* Nebula 1 — 蓝紫 */}
      <div style={{
        position: 'absolute', width: '80%', height: '70%',
        top: '-10%', right: '-20%',
        background: 'radial-gradient(ellipse at 60% 40%, rgba(124,58,237,0.12) 0%, rgba(14,165,233,0.06) 30%, transparent 60%)',
        filter: 'blur(60px)',
        animation: 'nebula-drift 20s ease-in-out infinite',
      }} />
      {/* Nebula 2 — 金 */}
      <div style={{
        position: 'absolute', width: '60%', height: '60%',
        bottom: '-10%', left: '-10%',
        background: 'radial-gradient(ellipse at 40% 60%, rgba(212,168,67,0.08) 0%, rgba(124,58,237,0.04) 30%, transparent 55%)',
        filter: 'blur(50px)',
        animation: 'nebula-drift 25s ease-in-out infinite reverse',
      }} />
      {/* Star dust layer — 微噪点 */}
      <div style={{
        position: 'absolute', inset: 0,
        opacity: 0.3,
        backgroundImage: 'radial-gradient(1px 1px at 20% 30%, #fff, transparent), radial-gradient(1px 1px at 40% 70%, #fff, transparent), radial-gradient(1.5px 1.5px at 60% 20%, #fff, transparent), radial-gradient(1px 1px at 80% 50%, #fff, transparent)',
        backgroundSize: '200px 200px',
      }} />
    </div>
  );
}

// ====================================================================
// 宇宙风格 Toast
// ====================================================================
function AstralToast({ message, type, onDone }: { message: string; type: 'success' | 'error' | 'info'; onDone: () => void }) {
  useEffect(() => { const t = setTimeout(onDone, 2200); return () => clearTimeout(t); }, [onDone]);

  const colors = {
    success: { border: 'rgba(212,168,67,0.4)', text: 'var(--gold-light)', shadow: 'rgba(212,168,67,0.2)' },
    error: { border: 'rgba(239,68,68,0.4)', text: '#ef4444', shadow: 'rgba(239,68,68,0.2)' },
    info: { border: 'rgba(14,165,233,0.4)', text: '#0ea5e9', shadow: 'rgba(14,165,233,0.2)' },
  };
  const c = colors[type];

  return (
    <motion.div
      initial={{ y: -50, opacity: 0, scale: 0.85 }}
      animate={{ y: 0, opacity: 1, scale: 1 }}
      exit={{ y: -50, opacity: 0, scale: 0.85 }}
      style={{
        position: 'fixed', top: 20, left: '50%', transform: 'translateX(-50%)',
        zIndex: 999,
        padding: '14px 32px',
        borderRadius: 16,
        background: 'rgba(10,5,32,0.85)',
        border: `1px solid ${c.border}`,
        backdropFilter: 'blur(20px)',
        boxShadow: `0 8px 32px ${c.shadow}, inset 0 1px 0 rgba(255,255,255,0.05)`,
        color: c.text,
        fontSize: 14,
        fontWeight: 600,
        fontFamily: 'var(--font-body), serif',
        letterSpacing: '0.5px',
        whiteSpace: 'nowrap',
      }}
    >
      {message}
    </motion.div>
  );
}

// ====================================================================
// 星轨按钮装饰 (纯 CSS)
// ====================================================================
function OrbitRing({ size = 100 }: { size?: number }) {
  return (
    <div style={{
      position: 'absolute', width: size, height: size,
      borderRadius: '50%',
      border: '1px solid rgba(212,168,67,0.12)',
      top: '50%', left: '50%',
      transform: 'translate(-50%, -50%)',
      animation: 'spin-slow 12s linear infinite',
      pointerEvents: 'none',
    }}>
      <div style={{
        position: 'absolute', top: -3, left: '50%', marginLeft: -2,
        width: 5, height: 5, borderRadius: '50%',
        background: 'var(--gold)',
        boxShadow: `0 0 8px ${'var(--gold)'}`,
      }} />
    </div>
  );
}

function OrbitRingReverse({ size = 130 }: { size?: number }) {
  return (
    <div style={{
      position: 'absolute', width: size, height: size,
      borderRadius: '50%',
      border: '1px dashed rgba(212,168,67,0.07)',
      top: '50%', left: '50%',
      transform: 'translate(-50%, -50%)',
      animation: 'spin-slow-reverse 18s linear infinite',
      pointerEvents: 'none',
    }}>
      <div style={{
        position: 'absolute', bottom: -3, left: '50%', marginLeft: -2,
        width: 4, height: 4, borderRadius: '50%',
        background: COSMIC.purpleLight,
        boxShadow: `0 0 6px ${COSMIC.purpleLight}`,
      }} />
    </div>
  );
}

// ====================================================================
// 快速时间按钮
// ====================================================================
const QUICK_TIMES = [
  { val: 10, icon: '⚡', label: '碎片' },
  { val: 25, icon: '☀', label: '专注' },
  { val: 45, icon: '🌊', label: '深度' },
  { val: 90, icon: '🔥', label: '马拉松' },
];

// ====================================================================
// 主组件
// ====================================================================
export default function GachaPage() {
  const { dispatch, getAvailableTasks, data } = useStore();
  const isDark = data.settings.theme.themeMode === 'dark';

  useFontLoader();

  const [minutes, setMinutes] = useState(25);
  const [sessionCtx] = useState<GachaSessionContext>(createSessionContext());
  const [drawResult, setDrawResult] = useState<DrawChoiceResult | null>(null);
  const [multiResults, setMultiResults] = useState<DrawChoiceResult[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showReplace, setShowReplace] = useState(false);
  const [replaceTaskId, setReplaceTaskId] = useState<number>(0);
  const [showTimer, setShowTimer] = useState(false);
  const [poolName, setPoolName] = useState('');
  const [meteorIntensity, setMeteorIntensity] = useState(1);

  const [toasts, setToasts] = useState<Array<{ id: number; message: string; type: 'success' | 'error' | 'info' }>>([]);
  const toastId = useRef(0);
  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = toastId.current++;
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);
  const removeToast = useCallback((id: number) => setToasts(prev => prev.filter(t => t.id !== id)), []);

  const headerRef = useRef<HTMLDivElement>(null);
  const poolsRef = useRef<HTMLDivElement>(null);
  const controlRef = useRef<HTMLDivElement>(null);

  const pool = getPoolForTime(minutes);
  const updatePoolHint = (m: number) => {
    const p = getPoolForTime(m);
    setPoolName(p ? GACHA_POOL_NAMES[p] || '' : '时间不足');
  };

  // GSAP 隆重入场
  useEffect(() => {
    const tl = gsap.timeline({ defaults: { ease: 'back.out(1.7)' } });
    if (headerRef.current) tl.fromTo(headerRef.current, { y: -30, opacity: 0, scale: 0.95 }, { y: 0, opacity: 1, scale: 1, duration: 0.5 }, 0.1);
    if (poolsRef.current) {
      tl.fromTo(poolsRef.current.children, { y: 30, opacity: 0, scale: 0.85 }, { y: 0, opacity: 1, scale: 1, duration: 0.5, stagger: 0.1 }, '-=0.2');
    }
    if (controlRef.current) {
      tl.fromTo(controlRef.current, { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4 }, '-=0.15');
    }
    return () => { tl.kill(); };
  }, []);

  const handleSingleDraw = () => {
    if (!pool) return;
    const available = getAvailableTasks();
    const poolTasks = filterByPool(available, pool);
    if (!poolTasks.length) return;
    const choices = getTopWeighted(poolTasks, 3, 'medium', sessionCtx);
    if (!choices.length) return;
    setDrawResult({ pool, choices, slotIndex: 0, isUrgent: isDdlUrgent(choices[0]) });
    setMultiResults([]);
    setSelectedTask(null);
    setShowTimer(false);
    setMeteorIntensity(prev => Math.min(prev + 0.5, 3));
    setTimeout(() => setMeteorIntensity(1), 4000);
    showToast('✦ 命运之轮转动，任务显现', 'success');
    dispatch({ type: 'RECORD_DRAW', taskId: choices[0].id });
  };

  const handleMultiDraw = () => {
    if (!pool) return;
    const plans = planMultiDraw(minutes);
    if (!plans.length) return;
    const available = getAvailableTasks();
    const results: DrawChoiceResult[] = [];
    for (const { pool: p, count } of plans) {
      const poolTasks = filterByPool(available, p);
      if (poolTasks.length) {
        const choices = getTopWeighted(poolTasks, Math.min(count * 2, 5), 'medium', sessionCtx);
        if (choices.length) {
          results.push({ pool: p, choices, slotIndex: results.length, isUrgent: isDdlUrgent(choices[0]) });
          dispatch({ type: 'RECORD_DRAW', taskId: choices[0].id });
        }
      }
    }
    setMultiResults(results);
    setDrawResult(null);
    setSelectedTask(null);
    setShowTimer(false);
    setMeteorIntensity(3);
    setTimeout(() => setMeteorIntensity(1), 5000);
    showToast(`✦ 群星连缀 · ${results.length} 组命运已交织`, 'success');
  };

  const handleSelectTask = (task: Task) => {
    setSelectedTask(task);
    setDrawResult(null);
    setMultiResults([]);
    dispatch({ type: 'SET_CURRENT_TASK', id: task.id });
    dispatch({ type: 'RECORD_GACHA', record: { id: Date.now(), timestamp: new Date().toISOString(), poolName: pool || 'unknown', availableTime: minutes, taskId: task.id, accepted: true } });
    setShowTimer(true);
  };

  const handleSkip = (originalTask: Task) => { setReplaceTaskId(originalTask.id); setShowReplace(true); setDrawResult(null); };
  const handleReplace = (reason: string) => {
    dispatch({ type: 'RECORD_REJECTION', entry: { id: Date.now(), taskId: replaceTaskId, reason, timestamp: new Date().toISOString() } });
    setShowReplace(false);
    handleSingleDraw();
  };
  const handleTimerComplete = () => {
    if (selectedTask) {
      dispatch({ type: 'COMPLETE_TASK', id: selectedTask.id });
      setSelectedTask(null);
      setShowTimer(false);
      showToast('✦ 天命已成 · 任务圆满完成', 'success');
    }
  };

  const availableTasks = getAvailableTasks();
  const plans = pool ? planMultiDraw(minutes) : [];
  const planSummary = plans.map(p => `${p.count}×${GACHA_POOL_NAMES[p.pool]}`).join(' + ');

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', gap: 18, overflow: 'auto', position: 'relative' }}>
      {/* 背景层 — 暗色模式显示星空，浅色模式用 CSS 变量背景 */}
      {isDark && <><NebulaBackground /><ConstellationField /><ShootingStars intensity={meteorIntensity} /></>}
      {!isDark && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
          background: 'var(--bg-deep)',
          opacity: 0.5,
        }} />
      )}

      {/* Toast */}
      <AnimatePresence>
        {toasts.map(t => <AstralToast key={t.id} message={t.message} type={t.type} onDone={() => removeToast(t.id)} />)}
      </AnimatePresence>

      {/* ===== 顶栏 ===== */}
      <div ref={headerRef} style={{ position: 'relative', zIndex: 5 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, marginBottom: 8 }}>
          <h1 style={{
            fontFamily: 'var(--font-display), serif',
            fontSize: 30, fontWeight: 700, lineHeight: 1.2,
            background: 'linear-gradient(135deg, #f0d878 0%, #d4a843 40%, #a07d2e 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            letterSpacing: '4px',
          }}>
            星穹之愿
          </h1>
          <div style={{
            fontFamily: 'var(--font-body), serif', fontSize: 13,
            color: 'var(--text-muted)', fontStyle: 'italic',
            paddingBottom: '4px',
          }}>
            — 天命择时，群星引路
          </div>
        </div>
        <StatusBar />
      </div>

      {/* ===== 星门卡池 ===== */}
      <div ref={poolsRef} style={{ position: 'relative', zIndex: 5, display: 'flex', gap: 10 }}>
        {Object.entries(POOL_CONFIG).map(([key, cfg]) => {
          const isActive = pool === key;
          const poolCount = isActive ? availableTasks.length : 0;
          const pMin = GACHA_POOL_RANGES[key]?.[0] || 0;
          const pMax = GACHA_POOL_RANGES[key]?.[1] || 0;
          return (
            <motion.div
              key={key}
              whileHover={{ y: -3, scale: 1.01 }}
              style={{
                flex: 1, padding: '16px 18px',
                borderRadius: 18,
                background: isActive ? cfg.gradient : 'rgba(255,255,255,0.02)',
                border: isActive ? 'none' : '1px solid rgba(255,255,255,0.06)',
                cursor: 'default',
                opacity: isActive ? 1 : 0.35,
                transition: 'opacity 0.3s ease',
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* 星芒背景 */}
              {isActive && (
                <div style={{
                  position: 'absolute', inset: 0,
                  background: `radial-gradient(ellipse at 50% 0%, ${cfg.glow.replace('0.5', '0.2')} 0%, transparent 60%)`,
                  pointerEvents: 'none',
                }} />
              )}
              <div style={{ fontSize: 22, marginBottom: 4, position: 'relative' }}>{cfg.icon}</div>
              <div style={{
                fontSize: 14, fontWeight: 700,
                color: isActive ? '#fff' : 'var(--text-secondary)',
                fontFamily: 'var(--font-heading), serif',
                letterSpacing: '1px',
                position: 'relative',
              }}>
                {GACHA_POOL_NAMES[key as GachaPool]}
              </div>
              <div style={{
                fontSize: 11,
                color: isActive ? 'rgba(255,255,255,0.6)' : 'var(--text-muted)',
                fontFamily: 'var(--font-body), serif',
                marginTop: 2, position: 'relative',
              }}>
                {pMin}–{pMax === 999 ? '∞' : pMax} 分钟 · {cfg.desc}
              </div>
              {isActive && poolCount > 0 && (
                <div style={{
                  marginTop: 6, fontSize: 11, fontWeight: 600,
                  color: 'rgba(255,255,255,0.8)',
                  fontFamily: 'var(--font-body), serif',
                  display: 'flex', alignItems: 'center', gap: 4,
                  position: 'relative',
                }}>
                  <Star size={10} fill="currentColor" />
                  可召唤·{poolCount} 个天命
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* ===== 控制台 ===== */}
      <div ref={controlRef} style={{ position: 'relative', zIndex: 5, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, flex: 1 }}>
        {/* 时间区 */}
        <div style={{
          background: 'var(--bg-card)',
          border: `1px solid ${'rgba(128,128,128,0.15)'}`,
          borderRadius: 20,
          padding: '18px 28px',
          display: 'flex', alignItems: 'center', gap: 16,
          width: '100%', maxWidth: 680, justifyContent: 'center',
          backdropFilter: 'blur(20px)',
          position: 'relative',
        }}>
          {/* 时间 + 卡池指示 */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: 13, fontFamily: 'var(--font-body), serif' }}>择时</span>
            <input
              type="number"
              value={minutes}
              onChange={e => { const m = Math.max(1, Math.min(480, parseInt(e.target.value) || 1)); setMinutes(m); updatePoolHint(m); }}
              style={{
                width: 60, padding: '4px 6px', borderRadius: 10,
                border: '2px solid rgba(212,168,67,0.3)',
                background: 'rgba(212,168,67,0.06)',
                color: 'var(--gold)', fontSize: 22, fontWeight: 700,
                textAlign: 'center', outline: 'none',
                fontFamily: 'var(--font-heading), serif',
                fontVariantNumeric: 'tabular-nums',
              }}
            />
            <span style={{ color: 'var(--text-secondary)', fontSize: 13, fontFamily: 'var(--font-body), serif' }}>分钟</span>
          </div>

          <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,0.06)' }} />

          {/* 快速时间 */}
          <div style={{ display: 'flex', gap: 4 }}>
            {QUICK_TIMES.map(q => (
              <motion.button
                key={q.val}
                whileHover={{ scale: 1.1, y: -1 }}
                whileTap={{ scale: 0.93 }}
                onClick={() => { setMinutes(q.val); updatePoolHint(q.val); }}
                style={{
                  padding: '6px 12px', borderRadius: 10,
                  border: `1px solid ${minutes === q.val ? 'rgba(212,168,67,0.4)' : 'rgba(255,255,255,0.06)'}`,
                  background: minutes === q.val ? 'rgba(212,168,67,0.12)' : 'rgba(255,255,255,0.02)',
                  color: minutes === q.val ? 'var(--gold)' : 'var(--text-muted)',
                  fontSize: 11, fontWeight: 600, cursor: 'pointer',
                  fontFamily: 'var(--font-heading), serif',
                  display: 'flex', alignItems: 'center', gap: 4,
                }}
              >
                <span>{q.icon}</span>
                <span>{q.val}</span>
              </motion.button>
            ))}
          </div>

          <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,0.06)' }} />

          {/* 卡池标签 */}
          <motion.div
            key={pool || 'none'}
            initial={{ scale: 0.8 }} animate={{ scale: 1 }}
            style={{
              padding: '5px 16px', borderRadius: 20,
              background: pool ? POOL_CONFIG[pool]?.gradient : 'rgba(239,68,68,0.15)',
              fontSize: 12, fontWeight: 700, color: '#fff',
              fontFamily: 'var(--font-heading), serif', letterSpacing: '1px',
            }}
          >
            {poolName || '时隙未定'}
          </motion.div>
        </div>

        {/* ===== 天命罗盘（抽卡按钮） ===== */}
        <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4, type: 'spring', stiffness: 120, damping: 14 }}
            style={{ position: 'relative', width: 180, height: 180 }}
          >
            {/* 星轨 */}
            <OrbitRingReverse size={150} />
            <OrbitRing size={120} />
            <OrbitRingReverse size={90} />

            {/* 主按钮 */}
            <motion.button
              onClick={handleSingleDraw}
              disabled={!pool || !availableTasks.length}
              whileTap={{ scale: 0.92 }}
              style={{
                position: 'absolute', top: '50%', left: '50%',
                transform: 'translate(-50%, -50%)',
                width: 80, height: 80, borderRadius: '50%',
                border: '2px solid rgba(212,168,67,0.4)',
                background: 'radial-gradient(circle at 40% 35%, rgba(212,168,67,0.2) 0%, rgba(10,5,32,0.9) 70%)',
                cursor: !pool || !availableTasks.length ? 'not-allowed' : 'pointer',
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                gap: 2,
                opacity: !pool || !availableTasks.length ? 0.35 : 1,
                color: 'var(--gold)',
                animation: !pool || !availableTasks.length ? 'none' : 'draw-pulse 3s ease-in-out infinite',
                zIndex: 2,
              }}
            >
              <div style={{
                position: 'absolute', inset: -8, borderRadius: '50%',
                background: 'conic-gradient(from 0deg, transparent, rgba(212,168,67,0.1), transparent, rgba(212,168,67,0.05), transparent)',
                animation: 'spin-slow 6s linear infinite',
                pointerEvents: 'none',
              }} />
              <Sparkles size={22} />
              <span style={{
                fontSize: 13, fontWeight: 700,
                fontFamily: 'var(--font-heading), serif',
                letterSpacing: '2px',
              }}>
                祈愿
              </span>
            </motion.button>

            {/* 连抽按钮 — 罗盘外缘 */}
            {pool && minutes >= 15 && (
              <motion.button
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.6, type: 'spring' }}
                onClick={handleMultiDraw}
                disabled={!availableTasks.length}
                style={{
                  position: 'absolute',
                  top: -8, right: -8,
                  width: 52, height: 52,
                  borderRadius: '50%',
                  border: '2px solid rgba(212,168,67,0.25)',
                  background: 'radial-gradient(circle at 40% 35%, rgba(212,168,67,0.12), rgba(10,5,32,0.8))',
                  cursor: availableTasks.length ? 'pointer' : 'not-allowed',
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  gap: 0,
                  opacity: availableTasks.length ? 1 : 0.35,
                  color: 'var(--gold)',
                  zIndex: 3,
                  padding: 0,
                }}
              >
                <ListOrdered size={14} />
                <span style={{ fontSize: 8, fontWeight: 700, fontFamily: 'var(--font-heading), serif', letterSpacing: '1px' }}>
                  连星
                </span>
              </motion.button>
            )}
          </motion.div>

          {/* 提示文字 */}
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 }}
            style={{
              fontFamily: 'var(--font-body), serif', fontStyle: 'italic',
              fontSize: 13, color: 'var(--text-muted)',
            }}
          >
            {!pool
              ? '⏳ 时隙不足，星辰尚未就位'
              : !availableTasks.length
                ? '🌙 卡池已空，待新天命降临'
                : `✦ 天命池中 · ${availableTasks.length} 个命运等待揭晓`
            }
          </motion.div>

          {/* 连抽方案提示 */}
          {pool && minutes >= 15 && planSummary && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              style={{
                padding: '6px 16px', borderRadius: 12,
                background: 'rgba(212,168,67,0.06)',
                border: '1px solid rgba(212,168,67,0.12)',
                fontSize: 11, color: 'var(--text-secondary)',
                fontFamily: 'var(--font-body), serif',
              }}
            >
              连星之阵 · {planSummary}
            </motion.div>
          )}
        </div>

        {/* ===== Timer ===== */}
        {showTimer && selectedTask && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ type: 'spring', damping: 20 }}
            style={{
              background: 'var(--bg-card)', border: `1px solid ${'rgba(128,128,128,0.15)'}`,
              borderRadius: 24, padding: 28,
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14,
              width: '100%', maxWidth: 360, position: 'relative',
              backdropFilter: 'blur(20px)',
            }}
          >
            <div style={{
              fontSize: 16, fontWeight: 700, fontFamily: 'var(--font-heading), serif',
              color: 'var(--text-primary)', textAlign: 'center', letterSpacing: '1px',
            }}>
              <span style={{ fontSize: 20, marginRight: 8 }}>✦</span>
              {selectedTask.name}
            </div>
            <Timer initialMinutes={Math.max(1, selectedTask.estimatedTime || 25)} onComplete={handleTimerComplete} />
            <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => { dispatch({ type: 'COMPLETE_TASK', id: selectedTask.id }); setSelectedTask(null); setShowTimer(false); showToast('✦ 天命已成 · 任务圆满完成', 'success'); }}
                style={{ padding: '8px 20px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #22c55e, #16a34a)', color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-body), serif' }}>
                ✅ 告成
              </motion.button>
              <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                onClick={() => { dispatch({ type: 'SKIP_TASK', id: selectedTask.id }); setSelectedTask(null); setShowTimer(false); }}
                style={{ padding: '8px 20px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.12)', background: 'none', color: 'var(--text-secondary)', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font-body), serif' }}>
                🔄 暂搁
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* ===== 抽卡结果 — 单抽 ===== */}
        <AnimatePresence>
          {drawResult && (
            <ChoiceDialog
              key="choice"
              pool={drawResult.pool}
              choices={drawResult.choices}
              isUrgent={drawResult.isUrgent}
              onSelect={handleSelectTask}
              onSkip={() => handleSkip(drawResult.choices[0])}
              onClose={() => setDrawResult(null)}
              getTaskRarity={getTaskRarity}
            />
          )}
        </AnimatePresence>

        {/* ===== 抽卡结果 — 连抽 ===== */}
        {multiResults.length > 0 && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ width: '100%', maxWidth: 700 }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14,
              fontFamily: 'var(--font-heading), serif', fontSize: 14,
              color: 'var(--text-secondary)', letterSpacing: '1px',
            }}>
              <Star size={16} color={'var(--gold)'} fill={'var(--gold)'} />
              连星之阵
              <span style={{ color: 'var(--gold)', fontWeight: 600 }}>{planSummary}</span>
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
              {multiResults.flatMap(r => r.choices.slice(0, 2)).map((task, i) => {
                const rarity = getTaskRarity(task);
                return (
                  <motion.div
                    key={`${task.id}-${i}`}
                    initial={{ opacity: 0, y: 30, scale: 0.85, rotateY: 30 }}
                    animate={{ opacity: 1, y: 0, scale: 1, rotateY: 0 }}
                    transition={{ delay: i * 0.12, type: 'spring', damping: 16, stiffness: 200 }}
                  >
                    <div style={{
                      width: 170, height: 230,
                      borderRadius: 18,
                      background: rarity.bg,
                      border: `1px solid ${rarity.glow}`,
                      display: 'flex', flexDirection: 'column',
                      alignItems: 'center', justifyContent: 'center',
                      gap: 8, padding: 18,
                      position: 'relative', overflow: 'hidden',
                    }}>
                      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: rarity.gradient }} />
                      <div style={{ fontSize: 13, color: '#f59e0b', letterSpacing: 3, fontFamily: 'var(--font-heading), serif' }}>
                        {'★'.repeat(rarity.stars)}
                      </div>
                      <div style={{
                        padding: '2px 14px', borderRadius: 10,
                        background: rarity.gradient, fontSize: 10, fontWeight: 700,
                        color: '#fff', fontFamily: 'var(--font-heading), serif', letterSpacing: '1px',
                      }}>
                        {rarity.label}
                      </div>
                      <div style={{
                        fontSize: 14, fontWeight: 700, color: 'var(--text-primary)',
                        textAlign: 'center', lineHeight: 1.3,
                        fontFamily: 'var(--font-body), serif',
                        display: '-webkit-box', WebkitLineClamp: 3,
                        WebkitBoxOrient: 'vertical', overflow: 'hidden',
                      }}>
                        {task.name}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-body), serif' }}>
                        ⏱ {task.estimatedTime} 分钟
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                        onClick={() => handleSelectTask(task)}
                        style={{
                          padding: '6px 20px', borderRadius: 8, border: 'none',
                          background: rarity.gradient, color: '#fff',
                          fontSize: 12, fontWeight: 700, cursor: 'pointer',
                          fontFamily: 'var(--font-heading), serif', letterSpacing: '1px',
                        }}
                      >
                        应命
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ===== 选中但未开始 ===== */}
        {selectedTask && !showTimer && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={() => { setShowTimer(true); dispatch({ type: 'SET_CURRENT_TASK', id: selectedTask.id }); }}
              style={{
                padding: '12px 36px', borderRadius: 12, border: 'none',
                background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 8,
                fontFamily: 'var(--font-heading), serif', letterSpacing: '1px',
                boxShadow: '0 4px 20px rgba(34,197,94,0.3)',
              }}>
              <TimerIcon size={18} />
              开启时计
            </motion.button>
          </motion.div>
        )}
      </div>

      {/* Replace dialog */}
      <AnimatePresence>
        {showReplace && (
          <ReplaceDialog taskId={replaceTaskId} onReplace={handleReplace} onCancel={() => setShowReplace(false)} />
        )}
      </AnimatePresence>
    </div>
  );
}
