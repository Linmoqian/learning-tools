import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, RotateCcw } from 'lucide-react';

interface TimerProps {
  initialMinutes: number;
  onComplete?: () => void;
  onTick?: (seconds: number) => void;
}

export default function Timer({ initialMinutes, onComplete, onTick }: TimerProps) {
  const [seconds, setSeconds] = useState(initialMinutes * 60);
  const [isActive, setIsActive] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  useEffect(() => {
    setSeconds(initialMinutes * 60);
    setIsActive(false);
    setHasStarted(false);
  }, [initialMinutes]);

  useEffect(() => {
    if (!isActive || seconds <= 0) return;
    const interval = setInterval(() => {
      setSeconds(s => {
        const next = s - 1;
        onTick?.(next);
        if (next <= 0) {
          setIsActive(false);
          onComplete?.();
          return 0;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isActive, seconds, onComplete, onTick]);

  const toggle = useCallback(() => {
    setIsActive(a => !a);
    if (!hasStarted) setHasStarted(true);
  }, [hasStarted]);

  const reset = useCallback(() => {
    setIsActive(false);
    setSeconds(initialMinutes * 60);
    setHasStarted(false);
  }, [initialMinutes]);

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  const progress = 1 - seconds / (initialMinutes * 60);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
      {/* Progress ring */}
      <div style={{ position: 'relative', width: 120, height: 120 }}>
        <svg width={120} height={120} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={60} cy={60} r={52} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={4} />
          <motion.circle
            cx={60}
            cy={60}
            r={52}
            fill="none"
            stroke={seconds === 0 ? '#27ae60' : '#f0c040'}
            strokeWidth={4}
            strokeLinecap="round"
            strokeDasharray={326.7}
            initial={{ strokeDashoffset: 326.7 }}
            animate={{ strokeDashoffset: 326.7 * (1 - progress) }}
            transition={{ duration: 0.5, ease: 'linear' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexDirection: 'column',
          }}
        >
          <span style={{ fontSize: 28, fontWeight: 700, color: '#f0e8da', fontVariantNumeric: 'tabular-nums' }}>
            {String(mins).padStart(2, '0')}:{String(secs).padStart(2, '0')}
          </span>
        </div>
      </div>

      {/* Controls */}
      <div style={{ display: 'flex', gap: 12 }}>
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={toggle}
          style={{
            width: 48,
            height: 48,
            borderRadius: '50%',
            border: '2px solid rgba(240,192,64,0.4)',
            background: 'rgba(240,192,64,0.1)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#f0c040',
          }}
        >
          {isActive ? <Pause size={20} /> : <Play size={20} />}
        </motion.button>

        {hasStarted && (
          <motion.button
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={reset}
            style={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              border: '2px solid rgba(255,255,255,0.2)',
              background: 'rgba(255,255,255,0.05)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#a8a0b8',
            }}
          >
            <RotateCcw size={18} />
          </motion.button>
        )}
      </div>
    </div>
  );
}
