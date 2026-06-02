import { useState, useEffect, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import { X, Sparkles } from 'lucide-react';
import { Task, GachaPool, GACHA_POOL_NAMES } from '../lib/types';

interface ChoiceDialogProps {
  pool: GachaPool;
  choices: Task[];
  isUrgent: boolean;
  onSelect: (task: Task) => void;
  onSkip: () => void;
  onClose: () => void;
  getTaskRarity: (task: Task) => { stars: number; label: string; gradient: string; glow: string; bg: string };
}

// ===== 星能迸发粒子 =====
function EnergyBurst({ x, y, color }: { x: number; y: number; color: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const particles: Array<{
      x: number; y: number; vx: number; vy: number;
      life: number; maxLife: number; size: number; hue: number;
    }> = [];

    const hue = parseInt(color.replace('#', ''), 16) % 360;
    for (let i = 0; i < 30; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 2 + Math.random() * 5;
      particles.push({
        x, y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 2,
        life: 0,
        maxLife: 30 + Math.random() * 40,
        size: 1.5 + Math.random() * 3,
        hue: hue + (Math.random() - 0.5) * 40,
      });
    }

    let frame: number;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let alive = false;
      particles.forEach(p => {
        p.life++;
        if (p.life > p.maxLife) return;
        alive = true;
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.05;
        const progress = p.life / p.maxLife;
        const alpha = 1 - progress;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size * (1 - progress * 0.5), 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${p.hue}, 80%, 65%, ${alpha})`;
        ctx.fill();
        ctx.shadowBlur = 8;
        ctx.shadowColor = `hsla(${p.hue}, 80%, 65%, ${alpha * 0.5})`;
      });
      if (alive) frame = requestAnimationFrame(animate);
    };
    animate();

    return () => cancelAnimationFrame(frame);
  }, [x, y, color]);

  return (
    <canvas
      ref={canvasRef}
      width={300}
      height={300}
      style={{ position: 'fixed', left: x - 150, top: y - 150, width: 300, height: 300, pointerEvents: 'none', zIndex: 200 }}
    />
  );
}

export default function ChoiceDialog({
  pool, choices, isUrgent, onSelect, onSkip, onClose, getTaskRarity,
}: ChoiceDialogProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});
  const [bursts, setBursts] = useState<Array<{ id: number; x: number; y: number; color: string }>>([]);
  const burstId = useRef(0);
  const dialogRef = useRef<HTMLDivElement>(null);

  // 交错翻牌
  useEffect(() => {
    choices.forEach((_, i) => {
      setTimeout(() => {
        setFlipped(prev => ({ ...prev, [i]: true }));
      }, 400 + i * 300);
    });
  }, [choices]);

  // 翻牌后触发星能迸发
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const cards = el.querySelectorAll('[data-card-container]');
    cards.forEach((card, i) => {
      const timeout = 400 + i * 300 + 350;
      setTimeout(() => {
        const rect = card.getBoundingClientRect();
        const rarity = getTaskRarity(choices[i]);
        const color = rarity.glow;
        setBursts(prev => [...prev, {
          id: burstId.current++,
          x: rect.left + rect.width / 2,
          y: rect.top + rect.height / 2,
          color,
        }]);
        // 清理迸发
        setTimeout(() => {
          setBursts(prev => prev.filter(b => b.id !== burstId.current - 1));
        }, 1200);
      }, timeout);
    });
  }, [choices, getTaskRarity]);

  // 背景星尘粒子
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const particles: HTMLDivElement[] = [];
    for (let i = 0; i < 16; i++) {
      const p = document.createElement('div');
      const size = 1.5 + Math.random() * 2;
      p.style.cssText = `
        position: absolute;
        width: ${size}px; height: ${size}px;
        background: ${['#d4a843', '#7c3aed', '#0ea5e9'][Math.floor(Math.random() * 3)]};
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: 0;
        pointer-events: none;
        filter: blur(0.5px);
      `;
      el.appendChild(p);
      particles.push(p);
      gsap.to(p, {
        opacity: 0.2 + Math.random() * 0.4,
        y: -(5 + Math.random() * 20),
        duration: 2 + Math.random() * 3,
        repeat: -1,
        delay: Math.random() * 3,
        ease: 'sine.inOut',
      });
    }
    return () => particles.forEach(p => p.remove());
  }, []);

  const handleBurstSelect = useCallback((task: Task, e: React.MouseEvent) => {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const rarity = getTaskRarity(task);
    setBursts(prev => [...prev, { id: burstId.current++, x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, color: rarity.glow }]);
    setTimeout(() => onSelect(task), 300);
  }, [onSelect, getTaskRarity]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed', inset: 0,
        background: 'radial-gradient(ellipse at 50% 50%, rgba(124,58,237,0.15) 0%, rgba(5,5,16,0.9) 60%)',
        backdropFilter: 'blur(16px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 100,
      }}
    >
      {/* 能量迸发层 */}
      {bursts.map(b => <EnergyBurst key={b.id} x={b.x} y={b.y} color={b.color} />)}

      <motion.div
        ref={dialogRef}
        initial={{ scale: 0.75, y: 80, opacity: 0, rotateX: 10 }}
        animate={{ scale: 1, y: 0, opacity: 1, rotateX: 0 }}
        exit={{ scale: 0.75, y: 80, opacity: 0 }}
        transition={{ type: 'spring', damping: 22, stiffness: 250 }}
        style={{
          background: 'linear-gradient(180deg, #0c0824 0%, #050510 100%)',
          border: '1px solid rgba(212,168,67,0.15)',
          borderRadius: 28,
          padding: '32px 36px',
          maxWidth: 820, width: '92vw',
          position: 'relative',
          overflow: 'hidden',
          boxShadow: '0 32px 80px rgba(0,0,0,0.6), inset 0 1px 0 rgba(212,168,67,0.06)',
        }}
      >
        {/* 顶部装饰 — 渐变光晕 */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 2,
          background: 'linear-gradient(90deg, transparent 0%, #d4a843 20%, #7c3aed 50%, #0ea5e9 80%, transparent 100%)',
          backgroundSize: '200% 100%',
          animation: 'shimmer 3s linear infinite',
        }} />

        {/* 右上角星芒关闭 */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 14, right: 14,
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.06)',
            borderRadius: '50%',
            width: 34, height: 34,
            cursor: 'pointer', color: COSMIC.textMuted,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 5,
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'rgba(212,168,67,0.15)'; e.currentTarget.style.color = COSMIC.gold; }}
          onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; e.currentTarget.style.color = COSMIC.textMuted; }}
        >
          <X size={18} />
        </button>

        {/* 标题区 */}
        <div style={{ textAlign: 'center', marginBottom: 28, position: 'relative', zIndex: 2 }}>
          <div style={{
            fontSize: 12, color: COSMIC.textMuted, marginBottom: 8,
            fontFamily: 'var(--font-body), serif', fontStyle: 'italic',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>
            <Sparkles size={12} color={COSMIC.gold} />
            来自{' '}
            <span style={{
              fontFamily: 'var(--font-heading), serif',
              color: COSMIC.gold, fontWeight: 600, fontStyle: 'normal',
              letterSpacing: '1px',
            }}>
              {GACHA_POOL_NAMES[pool] || pool}
            </span>
            {' '}的启示
          </div>
          <h2 style={{
            fontFamily: 'var(--font-display), serif',
            fontSize: 26, fontWeight: 700, lineHeight: 1.3,
            background: 'linear-gradient(135deg, #f0d878 0%, #d4a843 40%, #7c3aed 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            letterSpacing: '2px',
          }}>
            命运之示
          </h2>
        </div>

        {/* 紧急警示 */}
        {isUrgent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.2)',
              borderRadius: 12, padding: '10px 16px', marginBottom: 20,
              textAlign: 'center', position: 'relative', zIndex: 2,
            }}
          >
            <span style={{
              fontSize: 13, fontWeight: 700, color: '#ef4444',
              fontFamily: 'var(--font-heading), serif', letterSpacing: '1px',
            }}>
              ⏳ 天命将逝 · 此任务刻不容缓
            </span>
          </motion.div>
        )}

        {/* 卡牌区 */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', position: 'relative', zIndex: 2 }}>
          {choices.map((task, i) => {
            const rarity = getTaskRarity(task);
            const isFlipped = flipped[i];
            const isSelected = selected === task.id;

            return (
              <div
                key={task.id}
                data-card-container
                style={{ perspective: 1200, width: 190, height: 270 }}
              >
                <motion.div
                  animate={{
                    rotateY: isFlipped ? 0 : 180,
                    scale: isSelected ? 1.07 : 1,
                  }}
                  transition={{ duration: 0.55, ease: [0.23, 1, 0.32, 1] }}
                  style={{
                    width: '100%', height: '100%',
                    transformStyle: 'preserve-3d',
                    cursor: 'pointer', position: 'relative',
                  }}
                  onClick={() => setSelected(task.id)}
                >
                  {/* ===== 卡背（星辰封印） ===== */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    backfaceVisibility: 'hidden',
                    borderRadius: 20,
                    background: 'linear-gradient(145deg, #1a0a2e 0%, #0c0824 50%, #0a0520 100%)',
                    border: '2px solid rgba(212,168,67,0.15)',
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                    gap: 14, padding: 20,
                  }}>
                    {/* 中央星芒封印 */}
                    <div style={{
                      width: 60, height: 60,
                      borderRadius: '50%',
                      background: 'conic-gradient(from 0deg, rgba(212,168,67,0.2), rgba(124,58,237,0.2), rgba(212,168,67,0.2))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      animation: 'spin-slow 8s linear infinite',
                    }}>
                      <div style={{
                        width: 30, height: 30, borderRadius: '50%',
                        background: 'radial-gradient(circle, rgba(212,168,67,0.3), transparent)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 18,
                      }}>
                        ✦
                      </div>
                    </div>
                    <div style={{
                      fontFamily: 'var(--font-heading), serif',
                      fontSize: 13, fontWeight: 600,
                      color: 'rgba(212,168,67,0.6)',
                      letterSpacing: '3px',
                    }}>
                      第 {i + 1} 示
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      {[0, 1, 2].map(j => (
                        <div key={j} style={{
                          width: 5, height: 5, borderRadius: '50%',
                          background: j === 0 ? COSMIC.gold : j === 1 ? COSMIC.purple : COSMIC.blue,
                          opacity: 0.5,
                        }} />
                      ))}
                    </div>
                    {/* 四角星纹 */}
                    <div style={{ position: 'absolute', top: 12, left: 12, fontSize: 8, opacity: 0.3 }}>✦</div>
                    <div style={{ position: 'absolute', top: 12, right: 12, fontSize: 8, opacity: 0.3 }}>✦</div>
                    <div style={{ position: 'absolute', bottom: 12, left: 12, fontSize: 8, opacity: 0.3 }}>✦</div>
                    <div style={{ position: 'absolute', bottom: 12, right: 12, fontSize: 8, opacity: 0.3 }}>✦</div>
                  </div>

                  {/* ===== 卡面（天命揭示） ===== */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    backfaceVisibility: 'hidden',
                    borderRadius: 20,
                    background: rarity.bg,
                    border: `1.5px solid ${rarity.glow}`,
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center',
                    gap: 6, padding: 20,
                    overflow: 'hidden',
                    transform: 'rotateY(180deg)',
                    boxShadow: isSelected ? `0 0 30px ${rarity.glow}` : 'none',
                    transition: 'box-shadow 0.3s ease',
                  }}>
                    {/* 顶部品级条 */}
                    <div style={{
                      position: 'absolute', top: 0, left: 0, right: 0, height: 5,
                      background: rarity.gradient,
                    }} />

                    {/* 星级 — 弹簧弹出 */}
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={isFlipped ? { scale: 1, rotate: 0 } : {}}
                      transition={{ delay: 0.15, type: 'spring', damping: 10, stiffness: 150 }}
                      style={{
                        display: 'flex', gap: 2,
                        fontSize: 16, color: '#f59e0b',
                        letterSpacing: 4, marginTop: 4,
                      }}
                    >
                      {'★'.repeat(rarity.stars)}
                    </motion.div>

                    {/* 品级标签 */}
                    <div style={{
                      padding: '3px 16px', borderRadius: 10,
                      background: rarity.gradient,
                      fontSize: 11, fontWeight: 700, color: '#fff',
                      fontFamily: 'var(--font-heading), serif',
                      letterSpacing: '2px',
                    }}>
                      {rarity.label}
                    </div>

                    {/* 任务名称 */}
                    <div style={{
                      fontSize: 14, fontWeight: 700, color: COSMIC.textPrimary,
                      textAlign: 'center', lineHeight: 1.4, marginTop: 4,
                      fontFamily: 'var(--font-body), serif',
                      display: '-webkit-box', WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical', overflow: 'hidden',
                    }}>
                      {task.name}
                    </div>

                    {/* 时间 */}
                    <div style={{
                      fontSize: 12, color: COSMIC.textMuted,
                      fontFamily: 'var(--font-body), serif',
                    }}>
                      ⏱ {task.estimatedTime} 分钟
                    </div>

                    {/* 选定按钮 */}
                    <motion.button
                      whileHover={{ scale: 1.06 }}
                      whileTap={{ scale: 0.93 }}
                      onClick={e => handleBurstSelect(task, e)}
                      style={{
                        padding: '7px 24px', borderRadius: 10,
                        border: isSelected ? 'none' : '1px solid rgba(255,255,255,0.12)',
                        background: isSelected ? rarity.gradient : 'rgba(255,255,255,0.05)',
                        color: isSelected ? '#fff' : COSMIC.textSecondary,
                        fontSize: 13, fontWeight: 700, cursor: 'pointer', marginTop: 4,
                        fontFamily: 'var(--font-heading), serif',
                        letterSpacing: '1px',
                        transition: 'all 0.2s ease',
                        display: 'flex', alignItems: 'center', gap: 4,
                      }}
                    >
                      {isSelected ? '✦ 应允此命' : '选此天命'}
                    </motion.button>

                    {/* 选中时稀有度边框辉光 */}
                    {isSelected && (
                      <div style={{
                        position: 'absolute', inset: -2, borderRadius: 20,
                        border: '2px solid transparent',
                        background: `${rarity.gradient} border-box`,
                        WebkitMask: 'linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0)',
                        WebkitMaskComposite: 'xor', maskComposite: 'exclude',
                        pointerEvents: 'none',
                      }} />
                    )}
                  </div>
                </motion.div>
              </div>
            );
          })}
        </div>

        {/* 换牌 */}
        <div style={{ textAlign: 'center', marginTop: 24, position: 'relative', zIndex: 2 }}>
          <motion.button
            whileHover={{ scale: 1.03, borderColor: 'rgba(212,168,67,0.2)' }}
            whileTap={{ scale: 0.97 }}
            onClick={onSkip}
            style={{
              background: 'rgba(255,255,255,0.02)',
              border: '1px solid rgba(255,255,255,0.08)',
              borderRadius: 10, padding: '8px 28px',
              color: COSMIC.textMuted, fontSize: 13, cursor: 'pointer',
              fontFamily: 'var(--font-body), serif', fontStyle: 'italic',
              transition: 'all 0.2s ease',
            }}
          >
            ✖ 另寻天命
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}

// ===== 内联 COSMIC 常量（避免跨文件引用） =====
const COSMIC = {
  gold: '#d4a843',
  purple: '#7c3aed',
  blue: '#0ea5e9',
  textPrimary: '#f0e8da',
  textSecondary: '#a8a0b8',
  textMuted: '#6b6480',
};
