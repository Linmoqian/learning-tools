import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import gsap from 'gsap';
import { Sparkles } from 'lucide-react';

interface GachaButtonProps {
  onClick: () => void;
  disabled?: boolean;
  label?: string;
}

export default function GachaButton({ onClick, disabled, label = '抽卡' }: GachaButtonProps) {
  const ref = useRef<HTMLDivElement>(null);
  const btnRef = useRef<HTMLButtonElement>(null);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; angle: number; size: number }>>([]);
  const pId = useRef(0);

  // GSAP 呼吸脉冲
  useEffect(() => {
    const el = btnRef.current;
    if (!el || disabled) return;
    const tl = gsap.timeline({ repeat: -1, yoyo: true });
    tl.to(el, {
      scale: 1.03,
      boxShadow: '0 0 40px rgba(240,192,64,0.45), 0 0 60px rgba(240,192,64,0.15)',
      duration: 1.8,
      ease: 'sine.inOut',
    });
    return () => { tl.kill(); };
  }, [disabled]);

  // GSAP 悬停弹性
  useEffect(() => {
    const el = btnRef.current;
    if (!el || disabled) return;
    const onEnter = () => gsap.to(el, { scale: 1.06, duration: 0.35, ease: 'back.out(2)' });
    const onLeave = () => gsap.to(el, { scale: 1, duration: 0.4, ease: 'elastic.out(1, 0.3)' });
    el.addEventListener('mouseenter', onEnter);
    el.addEventListener('mouseleave', onLeave);
    return () => {
      el.removeEventListener('mouseenter', onEnter);
      el.removeEventListener('mouseleave', onLeave);
    };
  }, [disabled]);

  const burst = () => {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    const newParticles = Array.from({ length: 20 }, () => ({
      id: pId.current++,
      x: cx,
      y: cy,
      angle: Math.random() * 360,
      size: 2 + Math.random() * 4,
    }));
    setParticles(prev => [...prev, ...newParticles]);
    setTimeout(() => setParticles(prev => prev.filter(p => !newParticles.find(n => n.id === p.id))), 1000);
  };

  const handleClick = () => {
    burst();
    onClick();
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      {/* Particles */}
      {particles.map(p => (
        <motion.div
          key={p.id}
          initial={{ x: p.x, y: p.y, opacity: 1, scale: 1 }}
          animate={{
            x: p.x + Math.cos((p.angle * Math.PI) / 180) * 120,
            y: p.y + Math.sin((p.angle * Math.PI) / 180) * 120,
            opacity: 0,
            scale: 0,
          }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: p.size,
            height: p.size,
            borderRadius: '50%',
            background: '#f0c040',
            zIndex: 10,
            pointerEvents: 'none',
          }}
        />
      ))}

      <motion.button
        ref={btnRef}
        onClick={handleClick}
        disabled={disabled}
        whileTap={{ scale: disabled ? 1 : 0.92 }}
        style={{
          width: 180,
          height: 180,
          borderRadius: '50%',
          border: '3px solid rgba(240,192,64,0.5)',
          background: 'linear-gradient(135deg, rgba(240,192,64,0.15) 0%, rgba(240,192,64,0.05) 100%)',
          backdropFilter: 'blur(12px)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 4,
          position: 'relative',
          overflow: 'hidden',
          opacity: disabled ? 0.4 : 1,
        }}
      >
        {/* Inner glow */}
        <div
          style={{
            position: 'absolute',
            inset: 20,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(240,192,64,0.2) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        {/* Icon */}
        <Sparkles size={32} color="#f0c040" />

        {/* Label */}
        <span
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: '#f0c040',
            letterSpacing: 4,
            textShadow: '0 0 10px rgba(240,192,64,0.5)',
          }}
        >
          {label}
        </span>
      </motion.button>
    </div>
  );
}
