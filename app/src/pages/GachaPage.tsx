import { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { Clock, Sparkles, ListOrdered, Timer as TimerIcon } from 'lucide-react';
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

// ===== 卡池配置 =====
const POOL_CONFIG: Record<string, { gradient: string; glow: string; icon: string; desc: string }> = {
  [GachaPool.FRAGMENT]: {
    gradient: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
    glow: 'rgba(99, 102, 241, 0.4)',
    icon: '💎',
    desc: '短碎片时间',
  },
  [GachaPool.TOMATO]: {
    gradient: 'linear-gradient(135deg, #f59e0b, #f97316)',
    glow: 'rgba(245, 158, 11, 0.4)',
    icon: '🍅',
    desc: '专注番茄钟',
  },
  [GachaPool.DEEP]: {
    gradient: 'linear-gradient(135deg, #ef4444, #ec4899)',
    glow: 'rgba(239, 68, 68, 0.4)',
    icon: '🔥',
    desc: '深度工作',
  },
};

// ===== 稀有度配置 =====
const RARITY = [
  { stars: 5, label: '传说', gradient: 'linear-gradient(135deg, #f59e0b, #f97316)', glow: 'rgba(245,158,11,0.3)', bg: 'rgba(245,158,11,0.08)' },
  { stars: 4, label: '史诗', gradient: 'linear-gradient(135deg, #a855f7, #ec4899)', glow: 'rgba(168,85,247,0.3)', bg: 'rgba(168,85,247,0.08)' },
  { stars: 3, label: '稀有', gradient: 'linear-gradient(135deg, #3b82f6, #06b6d4)', glow: 'rgba(59,130,246,0.3)', bg: 'rgba(59,130,246,0.08)' },
  { stars: 2, label: '普通', gradient: 'linear-gradient(135deg, #6b7280, #9ca3af)', glow: 'rgba(107,114,128,0.3)', bg: 'rgba(107,114,128,0.08)' },
];

// ===== Toast 组件 =====
function Toast({ message, type, onDone }: { message: string; type: 'success' | 'error' | 'info'; onDone: () => void }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2000);
    return () => clearTimeout(t);
  }, [onDone]);

  const colors = {
    success: { bg: 'rgba(34,197,94,0.15)', border: 'rgba(34,197,94,0.3)', text: '#22c55e' },
    error: { bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.3)', text: '#ef4444' },
    info: { bg: 'rgba(59,130,246,0.15)', border: 'rgba(59,130,246,0.3)', text: '#3b82f6' },
  };
  const c = colors[type];

  return (
    <motion.div
      initial={{ y: -40, opacity: 0, scale: 0.9 }}
      animate={{ y: 0, opacity: 1, scale: 1 }}
      exit={{ y: -40, opacity: 0, scale: 0.9 }}
      style={{
        position: 'fixed',
        top: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 999,
        padding: '12px 28px',
        borderRadius: 14,
        background: c.bg,
        border: `1px solid ${c.border}`,
        backdropFilter: 'blur(12px)',
        color: c.text,
        fontSize: 14,
        fontWeight: 600,
        whiteSpace: 'nowrap',
      }}
    >
      {message}
    </motion.div>
  );
}

// ===== 浮动星星粒子 =====
function StarParticles() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const stars: HTMLDivElement[] = [];

    for (let i = 0; i < 40; i++) {
      const star = document.createElement('div');
      const size = 1 + Math.random() * 2;
      star.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${i % 5 === 0 ? '#f0c040' : '#64748b'};
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: ${0.2 + Math.random() * 0.5};
        pointer-events: none;
      `;
      container.appendChild(star);
      stars.push(star);

      gsap.to(star, {
        y: -(20 + Math.random() * 40),
        opacity: 0,
        duration: 3 + Math.random() * 4,
        repeat: -1,
        delay: Math.random() * 4,
        ease: 'none',
      });
    }

    return () => stars.forEach(s => s.remove());
  }, []);

  return <div ref={containerRef} style={{ position: 'fixed', inset: 0, overflow: 'hidden', zIndex: 0, pointerEvents: 'none' }} />;
}

// ===== 获取任务稀有度 =====
function getTaskRarity(task: Task) {
  // 紧急/DDL 任务 → 5星
  if (isDdlUrgent(task)) return RARITY[0];
  // 高优先级 → 4星
  if (task.priority >= 4) return RARITY[1];
  // 中等优先级 → 3星
  if (task.priority >= 2) return RARITY[2];
  // 低优先级 → 2星
  return RARITY[3];
}

export default function GachaPage() {
  const { dispatch, getAvailableTasks } = useStore();
  const pageRef = useRef<HTMLDivElement>(null);
  const headerRef = useRef<HTMLDivElement>(null);
  const poolsRef = useRef<HTMLDivElement>(null);

  // Toast state
  const [toasts, setToasts] = useState<Array<{ id: number; message: string; type: 'success' | 'error' | 'info' }>>([]);
  const toastId = useRef(0);

  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info') => {
    const id = toastId.current++;
    setToasts(prev => [...prev, { id, message, type }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const [minutes, setMinutes] = useState(25);
  const [sessionCtx] = useState<GachaSessionContext>(createSessionContext());
  const [drawResult, setDrawResult] = useState<DrawChoiceResult | null>(null);
  const [multiResults, setMultiResults] = useState<DrawChoiceResult[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showReplace, setShowReplace] = useState(false);
  const [replaceTaskId, setReplaceTaskId] = useState<number>(0);
  const [showTimer, setShowTimer] = useState(false);
  const [poolName, setPoolName] = useState('');

  const pool = getPoolForTime(minutes);

  const updatePoolHint = (m: number) => {
    const p = getPoolForTime(m);
    setPoolName(p ? GACHA_POOL_NAMES[p] || '' : '时间不足');
  };

  // GSAP 入场
  useEffect(() => {
    const tl = gsap.timeline();
    if (headerRef.current) {
      tl.fromTo(headerRef.current, { y: -20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.4, ease: 'back.out(1.7)' });
    }
    if (poolsRef.current) {
      const cards = poolsRef.current.children;
      if (cards.length) {
        tl.fromTo(cards, { y: 30, opacity: 0, scale: 0.9 }, {
          y: 0, opacity: 1, scale: 1, duration: 0.45, ease: 'back.out(1.7)', stagger: 0.08,
        }, '-=0.1');
      }
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
    showToast(`抽出了 ${choices.length} 个候选任务`, 'success');
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
    showToast(`连抽方案已生成，共 ${results.length} 组`, 'success');
  };

  const handleSelectTask = (task: Task) => {
    setSelectedTask(task);
    setDrawResult(null);
    setMultiResults([]);
    dispatch({ type: 'SET_CURRENT_TASK', id: task.id });
    dispatch({
      type: 'RECORD_GACHA',
      record: {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        poolName: pool || 'unknown',
        availableTime: minutes,
        taskId: task.id,
        accepted: true,
      },
    });
    setShowTimer(true);
  };

  const handleSkip = (originalTask: Task) => {
    setReplaceTaskId(originalTask.id);
    setShowReplace(true);
    setDrawResult(null);
  };

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
      showToast('🎉 任务完成！', 'success');
    }
  };

  const availableTasks = getAvailableTasks();
  const plans = pool ? planMultiDraw(minutes) : [];
  const planSummary = plans.map(p => `${p.count}×${GACHA_POOL_NAMES[p.pool]}`).join(' + ');

  return (
    <div ref={pageRef} style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', gap: 20, overflow: 'auto', position: 'relative' }}>
      <StarParticles />

      {/* Toast */}
      <AnimatePresence>
        {toasts.map(t => (
          <Toast key={t.id} message={t.message} type={t.type} onDone={() => removeToast(t.id)} />
        ))}
      </AnimatePresence>

      {/* Header */}
      <div ref={headerRef} style={{ position: 'relative', zIndex: 1 }}>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #f0c040, #f97316)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 18,
          }}>
            ✦
          </div>
          <span className="gradient-text" style={{ fontSize: 28 }}>星穹之愿</span>
        </h1>
        <StatusBar />
      </div>

      {/* Pool Cards */}
      <div ref={poolsRef} style={{ position: 'relative', zIndex: 1, display: 'flex', gap: 12 }}>
        {Object.entries(POOL_CONFIG).map(([key, cfg]) => {
          const [min, max] = GACHA_POOL_RANGES[key] || [0, 0];
          const count = pool === key ? availableTasks.length : 0;
          const isActive = pool === key;
          return (
            <motion.div
              key={key}
              whileHover={isActive ? { y: -2 } : { y: -1, opacity: 0.7 }}
              style={{
                flex: 1,
                padding: '14px 16px',
                borderRadius: 16,
                background: isActive ? cfg.gradient : 'rgba(255,255,255,0.04)',
                border: isActive ? 'none' : '1px solid rgba(255,255,255,0.08)',
                cursor: 'pointer',
                opacity: isActive ? 1 : 0.45,
                transition: 'all 0.3s ease',
                boxShadow: isActive ? `0 8px 32px ${cfg.glow}` : 'none',
              }}
            >
              <div style={{ fontSize: 20, marginBottom: 4 }}>{cfg.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: isActive ? '#fff' : '#a8a0b8' }}>
                {GACHA_POOL_NAMES[key as GachaPool]}
              </div>
              <div style={{ fontSize: 11, color: isActive ? 'rgba(255,255,255,0.7)' : '#6b6480', marginTop: 2 }}>
                {min}-{max === 999 ? '∞' : max} 分钟 · {cfg.desc}
              </div>
              {isActive && count > 0 && (
                <div style={{
                  marginTop: 6, fontSize: 11, fontWeight: 600, color: 'rgba(255,255,255,0.8)',
                  display: 'flex', alignItems: 'center', gap: 4,
                }}>
                  <Sparkles size={10} />
                  可抽取 {count} 个任务
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Main control area */}
      <div data-gacha-content style={{ position: 'relative', zIndex: 1, flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
        {/* Time + Draw buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="glass"
          style={{
            padding: '20px 32px',
            borderRadius: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            width: '100%',
            maxWidth: 640,
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Time input */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={18} color="#a8a0b8" />
            <span style={{ color: '#a8a0b8', fontSize: 13 }}>我有</span>
            <div style={{ position: 'relative' }}>
              <input
                type="number"
                value={minutes}
                onChange={e => {
                  const m = Math.max(1, Math.min(480, parseInt(e.target.value) || 1));
                  setMinutes(m);
                  updatePoolHint(m);
                }}
                style={{
                  width: 64,
                  padding: '6px 8px',
                  borderRadius: 10,
                  border: '2px solid rgba(240,192,64,0.3)',
                  background: 'rgba(240,192,64,0.06)',
                  color: '#f0c040',
                  fontSize: 22,
                  fontWeight: 800,
                  textAlign: 'center',
                  outline: 'none',
                  fontVariantNumeric: 'tabular-nums',
                }}
              />
            </div>
            <span style={{ color: '#a8a0b8', fontSize: 13 }}>分钟</span>
          </div>

          {/* Pool indicator */}
          <motion.div
            key={pool || 'none'}
            initial={{ scale: 0.8 }}
            animate={{ scale: 1 }}
            style={{
              padding: '4px 14px',
              borderRadius: 20,
              background: pool ? `${POOL_CONFIG[pool]?.gradient || '#6366f1'}` : 'rgba(239,68,68,0.2)',
              fontSize: 12,
              fontWeight: 700,
              color: '#fff',
              whiteSpace: 'nowrap',
            }}
          >
            {poolName || '⛔ 时间不足'}
          </motion.div>

          {/* Quick time buttons */}
          <div style={{ display: 'flex', gap: 4 }}>
            {[10, 25, 45, 90].map(t => (
              <motion.button
                key={t}
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.92 }}
                onClick={() => { setMinutes(t); updatePoolHint(t); }}
                style={{
                  padding: '4px 10px',
                  borderRadius: 8,
                  border: `1px solid ${minutes === t ? 'rgba(240,192,64,0.5)' : 'rgba(255,255,255,0.08)'}`,
                  background: minutes === t ? 'rgba(240,192,64,0.12)' : 'rgba(255,255,255,0.03)',
                  color: minutes === t ? '#f0c040' : '#6b6480',
                  fontSize: 11,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {t}分
              </motion.button>
            ))}
          </div>

          {/* Draw buttons */}
          <div style={{ display: 'flex', gap: 8 }}>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.93 }}
              onClick={handleSingleDraw}
              disabled={!pool || !availableTasks.length}
              style={{
                padding: '10px 22px',
                borderRadius: 12,
                border: 'none',
                background: !pool || !availableTasks.length
                  ? 'rgba(255,255,255,0.05)'
                  : 'linear-gradient(135deg, #f0c040, #f97316)',
                color: !pool || !availableTasks.length ? '#6b6480' : '#0a0e1a',
                fontSize: 14,
                fontWeight: 700,
                cursor: !pool || !availableTasks.length ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                boxShadow: pool && availableTasks.length ? '0 4px 20px rgba(240,192,64,0.3)' : 'none',
              }}
            >
              <Sparkles size={16} />
              单抽
            </motion.button>

            {pool && minutes >= 15 && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.93 }}
                onClick={handleMultiDraw}
                disabled={!availableTasks.length}
                style={{
                  padding: '10px 18px',
                  borderRadius: 12,
                  border: '2px solid rgba(240,192,64,0.3)',
                  background: 'rgba(240,192,64,0.06)',
                  color: availableTasks.length ? '#f0c040' : '#6b6480',
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: availableTasks.length ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: 0,
                  opacity: availableTasks.length ? 1 : 0.4,
                }}
              >
                <ListOrdered size={16} />
                <span>连抽</span>
                {planSummary && (
                  <span style={{ fontSize: 8, fontWeight: 500, opacity: 0.7 }}>{planSummary}</span>
                )}
              </motion.button>
            )}
          </div>
        </motion.div>

        {/* Available count */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.35 }}
          style={{
            padding: '8px 20px',
            borderRadius: 20,
            background: 'rgba(240,192,64,0.08)',
            border: '1px solid rgba(240,192,64,0.15)',
            fontSize: 13,
            color: '#a8a0b8',
          }}
        >
          卡池待命{' '}
          <strong style={{ color: '#f0c040', fontSize: 16 }}>{availableTasks.length}</strong>
          {' '}个任务
        </motion.div>

        {/* Timer */}
        {showTimer && selectedTask && (
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="glass"
            style={{
              padding: 28,
              borderRadius: 24,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 14,
              width: '100%',
              maxWidth: 360,
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Task name */}
            <div style={{ fontSize: 16, fontWeight: 700, color: '#f0e8da', textAlign: 'center' }}>
              <span style={{ fontSize: 24, marginRight: 8 }}>🎯</span>
              {selectedTask.name}
            </div>
            <Timer
              initialMinutes={Math.max(1, selectedTask.estimatedTime || 25)}
              onComplete={handleTimerComplete}
            />
            <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  dispatch({ type: 'COMPLETE_TASK', id: selectedTask.id });
                  setSelectedTask(null);
                  setShowTimer(false);
                  showToast('🎉 任务完成！', 'success');
                }}
                style={{
                  padding: '8px 20px',
                  borderRadius: 10,
                  border: 'none',
                  background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                  color: '#fff',
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}
              >
                ✅ 完成
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  dispatch({ type: 'SKIP_TASK', id: selectedTask.id });
                  setSelectedTask(null);
                  setShowTimer(false);
                }}
                style={{
                  padding: '8px 20px',
                  borderRadius: 10,
                  border: '1px solid rgba(255,255,255,0.12)',
                  background: 'none',
                  color: '#a8a0b8',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                🔄 跳过
              </motion.button>
            </div>
          </motion.div>
        )}

        {/* Draw Result - Single */}
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

        {/* Draw Result - Multi */}
        {multiResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ width: '100%', maxWidth: 700 }}
          >
            <div style={{
              display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14,
              fontSize: 14, color: '#a8a0b8',
            }}>
              <ListOrdered size={18} color="#f0c040" />
              连抽方案
              <span style={{ fontSize: 12, color: '#6b6480' }}>|</span>
              <span style={{ color: '#f0c040', fontWeight: 600 }}>{planSummary}</span>
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
              {multiResults.flatMap(r => r.choices.slice(0, 2)).map((task, i) => {
                const rarity = getTaskRarity(task);
                return (
                  <motion.div
                    key={`${task.id}-${i}`}
                    initial={{ opacity: 0, y: 30, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    transition={{ delay: i * 0.1, type: 'spring', damping: 15, stiffness: 200 }}
                    style={{ textAlign: 'center' }}
                  >
                    <div
                      style={{
                        width: 160, height: 220,
                        borderRadius: 16,
                        background: rarity.bg,
                        border: `2px solid ${rarity.glow}`,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: 8,
                        padding: 16,
                        position: 'relative',
                        overflow: 'hidden',
                      }}
                    >
                      {/* Rarity gradient top */}
                      <div style={{
                        position: 'absolute', top: 0, left: 0, right: 0, height: 4,
                        background: rarity.gradient,
                      }} />
                      {/* Stars */}
                      <div style={{ fontSize: 12, color: '#f59e0b', letterSpacing: 2 }}>
                        {'★'.repeat(rarity.stars)}
                      </div>
                      <div style={{
                        fontSize: 14, fontWeight: 700, color: '#f0e8da',
                        textAlign: 'center', lineHeight: 1.3,
                      }}>
                        {task.name}
                      </div>
                      <div style={{ fontSize: 11, color: '#a8a0b8' }}>
                        ⏱ {task.estimatedTime} 分钟
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleSelectTask(task)}
                        style={{
                          padding: '6px 18px',
                          borderRadius: 8,
                          border: 'none',
                          background: rarity.gradient,
                          color: '#fff',
                          fontSize: 11,
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        ▶ 开始
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* Single selected task preview */}
        {selectedTask && !showTimer && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center' }}
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setShowTimer(true);
                dispatch({ type: 'SET_CURRENT_TASK', id: selectedTask.id });
              }}
              style={{
                marginTop: 12,
                padding: '12px 36px',
                borderRadius: 12,
                border: 'none',
                background: 'linear-gradient(135deg, #22c55e, #16a34a)',
                color: '#fff',
                fontSize: 15,
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <TimerIcon size={18} />
              开始番茄钟
            </motion.button>
          </motion.div>
        )}
      </div>

      {/* Replace dialog */}
      <AnimatePresence>
        {showReplace && (
          <ReplaceDialog
            taskId={replaceTaskId}
            onReplace={handleReplace}
            onCancel={() => setShowReplace(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
