import { useState, useEffect, useRef } from 'react';
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

export default function ChoiceDialog({
  pool,
  choices,
  isUrgent,
  onSelect,
  onSkip,
  onClose,
  getTaskRarity,
}: ChoiceDialogProps) {
  const [selected, setSelected] = useState<number | null>(null);
  const [flipped, setFlipped] = useState<Record<number, boolean>>({});
  const dialogRef = useRef<HTMLDivElement>(null);

  // 卡片依次翻牌动画
  useEffect(() => {
    choices.forEach((_, i) => {
      setTimeout(() => {
        setFlipped(prev => ({ ...prev, [i]: true }));
      }, 300 + i * 250);
    });
  }, [choices]);

  // Stars 粒子
  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    const particles: HTMLDivElement[] = [];
    for (let i = 0; i < 20; i++) {
      const p = document.createElement('div');
      const size = 2 + Math.random() * 3;
      p.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${Math.random() > 0.5 ? '#f0c040' : '#a855f7'};
        border-radius: 50%;
        left: ${Math.random() * 100}%;
        top: ${Math.random() * 100}%;
        opacity: 0;
        pointer-events: none;
      `;
      el.appendChild(p);
      particles.push(p);
      gsap.to(p, {
        opacity: 0.3 + Math.random() * 0.5,
        y: -(10 + Math.random() * 30),
        duration: 2 + Math.random() * 3,
        repeat: -1,
        delay: Math.random() * 3,
        ease: 'none',
      });
    }
    return () => particles.forEach(p => p.remove());
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.75)',
        backdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
    >
      <motion.div
        ref={dialogRef}
        initial={{ scale: 0.8, y: 60, opacity: 0 }}
        animate={{ scale: 1, y: 0, opacity: 1 }}
        exit={{ scale: 0.8, y: 60, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        style={{
          background: 'linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%)',
          border: '1px solid rgba(240,192,64,0.15)',
          borderRadius: 28,
          padding: '32px 36px',
          maxWidth: 780,
          width: '90vw',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Header decoration */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, height: 3,
          background: 'linear-gradient(90deg, #f0c040, #a855f7, #3b82f6, #f0c040)',
          backgroundSize: '300% 100%',
        }} />

        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: 14, right: 14,
            background: 'rgba(255,255,255,0.06)',
            border: 'none',
            borderRadius: '50%',
            width: 32, height: 32,
            cursor: 'pointer',
            color: '#a8a0b8',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 2,
          }}
        >
          <X size={18} />
        </button>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 28, position: 'relative', zIndex: 1 }}>
          <div style={{
            fontSize: 12, color: '#a8a0b8', marginBottom: 6,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
          }}>
            <Sparkles size={14} color="#f0c040" />
            <span>来自 <strong style={{ color: '#f0c040' }}>{GACHA_POOL_NAMES[pool] || pool}</strong></span>
          </div>
          <h2 style={{
            fontSize: 24, fontWeight: 800,
            background: 'linear-gradient(135deg, #f0c040, #a855f7)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            命运为你揭示了这些任务
          </h2>
        </div>

        {/* Urgent warning */}
        {isUrgent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            style={{
              background: 'rgba(239,68,68,0.12)',
              border: '1px solid rgba(239,68,68,0.25)',
              borderRadius: 12,
              padding: '8px 16px',
              marginBottom: 20,
              textAlign: 'center',
              fontSize: 13,
              fontWeight: 600,
              color: '#ef4444',
              position: 'relative', zIndex: 1,
            }}
          >
            ⏰ 紧急任务！截止时间马上到了
          </motion.div>
        )}

        {/* Cards with flip */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap', position: 'relative', zIndex: 1 }}>
          {choices.map((task, i) => {
            const rarity = getTaskRarity(task);
            const isFlipped = flipped[i];

            return (
              <div key={task.id} style={{ perspective: 1000, width: 180, height: 260 }}>
                <motion.div
                  animate={{
                    rotateY: isFlipped ? 0 : 180,
                    scale: selected === task.id ? 1.06 : 1,
                  }}
                  transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
                  style={{
                    width: '100%', height: '100%',
                    transformStyle: 'preserve-3d',
                    cursor: 'pointer',
                    position: 'relative',
                  }}
                  onClick={() => setSelected(task.id)}
                >
                  {/* Card Back (显示在翻转前) */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    backfaceVisibility: 'hidden',
                    borderRadius: 18,
                    background: 'linear-gradient(135deg, #2a1a3e, #1a1a2e)',
                    border: '2px solid rgba(168,85,247,0.3)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 12,
                  }}>
                    <div style={{
                      width: 50, height: 50, borderRadius: '50%',
                      background: 'linear-gradient(135deg, #f0c040, #a855f7)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: 24,
                    }}>
                      ★
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#a8a0b8' }}>
                      第 {i + 1} 张
                    </div>
                    <div style={{ display: 'flex', gap: 3 }}>
                      {[0, 1, 2].map(j => (
                        <div key={j} style={{
                          width: 6, height: 6, borderRadius: '50%',
                          background: j === 0 ? '#f0c040' : j === 1 ? '#a855f7' : '#3b82f6',
                        }} />
                      ))}
                    </div>
                  </div>

                  {/* Card Front */}
                  <div style={{
                    position: 'absolute', inset: 0,
                    backfaceVisibility: 'hidden',
                    borderRadius: 18,
                    background: rarity.bg,
                    border: `2px solid ${rarity.glow}`,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                    padding: 20,
                    overflow: 'hidden',
                    transform: 'rotateY(180deg)',
                  }}>
                    {/* Rarity top bar */}
                    <div style={{
                      position: 'absolute', top: 0, left: 0, right: 0, height: 4,
                      background: rarity.gradient,
                    }} />

                    {/* Rarity stars */}
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={isFlipped ? { scale: 1, rotate: 0 } : {}}
                      transition={{ delay: 0.2, type: 'spring', damping: 12 }}
                      style={{
                        display: 'flex', gap: 2, fontSize: 14,
                        color: '#f59e0b', letterSpacing: 3,
                      }}
                    >
                      {'★'.repeat(rarity.stars)}
                    </motion.div>

                    {/* Rarity label */}
                    <div style={{
                      padding: '2px 12px', borderRadius: 10,
                      background: rarity.gradient,
                      fontSize: 10, fontWeight: 700, color: '#fff',
                    }}>
                      {rarity.label}
                    </div>

                    {/* Task name */}
                    <div style={{
                      fontSize: 13, fontWeight: 700, color: '#f0e8da',
                      textAlign: 'center', lineHeight: 1.3,
                      display: '-webkit-box',
                      WebkitLineClamp: 3,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                    }}>
                      {task.name}
                    </div>

                    {/* Time */}
                    <div style={{ fontSize: 11, color: '#a8a0b8' }}>
                      ⏱ {task.estimatedTime} 分钟
                    </div>

                    {/* Select button */}
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={e => {
                        e.stopPropagation();
                        onSelect(task);
                      }}
                      style={{
                        padding: '6px 20px',
                        borderRadius: 10,
                        border: 'none',
                        background: selected === task.id ? rarity.gradient : 'rgba(255,255,255,0.08)',
                        color: selected === task.id ? '#fff' : '#a8a0b8',
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: 'pointer',
                        marginTop: 4,
                      }}
                    >
                      {selected === task.id ? '✨ 选中' : '选这个'}
                    </motion.button>

                    {/* Glow effect on hover */}
                    {selected === task.id && (
                      <div style={{
                        position: 'absolute', inset: -2,
                        borderRadius: 18,
                        border: '3px solid transparent',
                        background: `${rarity.gradient} border-box`,
                        WebkitMask: 'linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0)',
                        WebkitMaskComposite: 'xor',
                        maskComposite: 'exclude',
                        pointerEvents: 'none',
                      }} />
                    )}
                  </div>
                </motion.div>
              </div>
            );
          })}
        </div>

        {/* Skip footer */}
        <div style={{ textAlign: 'center', marginTop: 24, position: 'relative', zIndex: 1 }}>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onSkip}
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10,
              padding: '8px 24px',
              color: '#6b6480',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            ✖ 换一批任务
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
