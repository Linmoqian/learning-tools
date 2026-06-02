import { motion } from 'framer-motion';
import { Clock, Zap, Dumbbell, AlertTriangle } from 'lucide-react';
import { Task } from '../lib/types';
import { isDdlUrgent } from '../lib/algorithms';

interface TaskCardProps {
  task: Task;
  index?: number;
  onClick?: () => void;
  showActions?: boolean;
  compact?: boolean;
}

const profileColorMap: Record<string, string> = {
  daily_habit: '#7f8c8d',
  weekly_routine: '#27ae60',
  deadline_flexible: '#2980b9',
  deadline_progressive: '#e74c3c',
};

const energyLabel: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
};

const resistanceLabel: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
};

export default function TaskCard({ task, index = 0, onClick, compact = false }: TaskCardProps) {
  const urgent = isDdlUrgent(task);
  const color = profileColorMap[task.taskProfile] || '#2980b9';

  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        ease: [0.25, 0.1, 0.25, 1],
      }}
      whileHover={{ y: -6, transition: { duration: 0.2 } }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      style={{
        width: compact ? 160 : 200,
        height: compact ? 220 : 280,
        background: `linear-gradient(180deg,
          ${color}dd 0%,
          ${color}99 40%,
          rgba(200, 220, 255, 0.3) 70%,
          rgba(255, 255, 255, 0.15) 100%)`,
        border: '1px solid rgba(255,255,255,0.25)',
        borderRadius: 16,
        cursor: onClick ? 'pointer' : 'default',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        padding: compact ? '14px 12px 10px' : '18px 16px 12px',
      }}
    >
      {/* Glass overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(2px)',
          borderRadius: 16,
          pointerEvents: 'none',
        }}
      />

      {/* Urgent badge */}
      {urgent && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            background: '#e74c3c',
            borderRadius: 10,
            padding: '2px 8px',
            fontSize: 10,
            fontWeight: 700,
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            zIndex: 2,
          }}
        >
          <AlertTriangle size={10} />
          紧急
        </motion.div>
      )}

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 1, flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            fontSize: compact ? 13 : 15,
            fontWeight: 700,
            color: urgent ? '#fff' : '#1a1a2e',
            lineHeight: 1.3,
            display: '-webkit-box',
            WebkitLineClamp: compact ? 2 : 3,
            WebkitBoxOrient: 'vertical',
            overflow: 'hidden',
            textShadow: urgent ? '0 1px 3px rgba(0,0,0,0.3)' : '0 1px 2px rgba(255,255,255,0.3)',
            marginBottom: 4,
          }}
        >
          {task.name}
        </div>

        {!compact && task.tags.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, marginTop: 4 }}>
            {task.tags.slice(0, 3).map(tag => (
              <span
                key={tag}
                style={{
                  background: 'rgba(255,255,255,0.2)',
                  borderRadius: 8,
                  padding: '1px 6px',
                  fontSize: 9,
                  color: 'rgba(0,0,0,0.6)',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        <div style={{ flex: 1 }} />

        {/* Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 2 : 4 }}>
          <StatRow icon={<Zap size={compact ? 10 : 12} />} label={`阻力 ${resistanceLabel[task.resistance]}`} compact={compact} />
          <StatRow icon={<Dumbbell size={compact ? 10 : 12} />} label={`精力 ${energyLabel[task.energyRequired]}`} compact={compact} />
        </div>

        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 4,
            marginTop: compact ? 4 : 8,
            fontSize: compact ? 11 : 13,
            fontWeight: 700,
            color: 'rgba(0,0,0,0.7)',
          }}
        >
          <Clock size={compact ? 11 : 13} />
          {task.estimatedTime} 分钟
        </div>
      </div>

      {/* Shimmer on hover */}
      <motion.div
        style={{
          position: 'absolute',
          inset: 0,
          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent)',
          backgroundSize: '200% 100%',
          borderRadius: 16,
          pointerEvents: 'none',
          opacity: 0,
        }}
        whileHover={{ opacity: 1 }}
        animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      />
    </motion.div>
  );
}

function StatRow({ icon, label, compact }: { icon: React.ReactNode; label: string; compact: boolean }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'rgba(0,0,0,0.6)', fontSize: compact ? 9 : 11 }}>
      {icon}
      <span>{label}</span>
    </div>
  );
}
