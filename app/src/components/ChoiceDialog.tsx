import { useState } from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import TaskCard from './TaskCard';
import { Task, GachaPool, GACHA_POOL_NAMES } from '../lib/types';

interface ChoiceDialogProps {
  pool: GachaPool;
  choices: Task[];
  isUrgent: boolean;
  onSelect: (task: Task) => void;
  onSkip: () => void;
  onClose: () => void;
}

export default function ChoiceDialog({
  pool,
  choices,
  isUrgent,
  onSelect,
  onSkip,
  onClose,
}: ChoiceDialogProps) {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
      }}
    >
      <motion.div
        initial={{ scale: 0.85, y: 40 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.85, y: 40 }}
        style={{
          background: 'linear-gradient(180deg, #1a2038 0%, #0f1422 100%)',
          border: '1px solid rgba(240,192,64,0.2)',
          borderRadius: 24,
          padding: '32px 40px',
          maxWidth: 800,
          width: '90vw',
          position: 'relative',
        }}
      >
        {/* Close */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            background: 'none',
            border: 'none',
            color: '#a8a0b8',
            cursor: 'pointer',
            padding: 4,
          }}
        >
          <X size={20} />
        </button>

        {/* Title */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 12, color: '#a8a0b8', marginBottom: 4 }}>
            来自 {GACHA_POOL_NAMES[pool] || pool}
          </div>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: '#f0e8da' }}>选择你的任务</h2>
        </div>

        {/* Urgent warning */}
        {isUrgent && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            style={{
              background: 'rgba(231,76,60,0.15)',
              border: '1px solid rgba(231,76,60,0.3)',
              borderRadius: 10,
              padding: '8px 16px',
              marginBottom: 20,
              textAlign: 'center',
              fontSize: 14,
              fontWeight: 600,
              color: '#e74c3c',
            }}
          >
            ⏰ 这个任务的截止时间马上到了！
          </motion.div>
        )}

        {/* Cards */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
          {choices.map((task, i) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 40, rotateY: 90 }}
              animate={{
                opacity: 1,
                y: 0,
                rotateY: 0,
                scale: selected === task.id ? 1.05 : 1,
              }}
              transition={{ delay: i * 0.12 + 0.2, duration: 0.4 }}
              style={{ cursor: 'pointer' }}
              onClick={() => setSelected(task.id)}
            >
              <TaskCard task={task} index={i} />

              {/* Select button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={e => {
                  e.stopPropagation();
                  onSelect(task);
                }}
                style={{
                  width: '100%',
                  marginTop: 8,
                  padding: '8px 0',
                  borderRadius: 8,
                  border: 'none',
                  background: selected === task.id
                    ? 'linear-gradient(135deg, #f0c040, #c99f2e)'
                    : 'rgba(255,255,255,0.1)',
                  color: selected === task.id ? '#0a0e1a' : '#a8a0b8',
                  fontSize: 13,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ✅ 选这个
              </motion.button>
            </motion.div>
          ))}
        </div>

        {/* Skip */}
        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSkip}
            style={{
              background: 'none',
              border: '1px solid rgba(255,255,255,0.15)',
              borderRadius: 8,
              padding: '8px 24px',
              color: '#a8a0b8',
              fontSize: 13,
              cursor: 'pointer',
            }}
          >
            ✖ 都不想要
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
