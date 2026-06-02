import { motion } from 'framer-motion';

interface ReplaceDialogProps {
  taskId: number;
  onReplace: (reason: string) => void;
  onCancel: () => void;
}

const REASONS = [
  { value: 'low_energy', label: '🪫 精力不足' },
  { value: 'no_time', label: '⏰ 时间不够' },
  { value: 'similar_done', label: '🔄 刚做过类似任务' },
  { value: 'other', label: '💬 其他' },
];

export default function ReplaceDialog({ onReplace, onCancel }: ReplaceDialogProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 110,
      }}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.9, y: 20 }}
        style={{
          background: 'linear-gradient(180deg, #1a2038, #0f1422)',
          border: '1px solid rgba(240,192,64,0.15)',
          borderRadius: 20,
          padding: '28px 32px',
          width: 360,
          textAlign: 'center',
        }}
      >
        <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f0e8da', marginBottom: 8 }}>
          为什么想换？
        </h3>
        <p style={{ fontSize: 13, color: '#a8a0b8', marginBottom: 20 }}>
          说说原因，系统会记下你的偏好
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {REASONS.map(r => (
            <motion.button
              key={r.value}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onReplace(r.value)}
              style={{
                background: 'rgba(255,255,255,0.05)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 10,
                padding: '10px 16px',
                color: '#f0e8da',
                fontSize: 14,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              {r.label}
            </motion.button>
          ))}
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onCancel}
          style={{
            marginTop: 16,
            background: 'none',
            border: 'none',
            color: '#6b6480',
            fontSize: 13,
            cursor: 'pointer',
          }}
        >
          算了，回去看看
        </motion.button>
      </motion.div>
    </motion.div>
  );
}
