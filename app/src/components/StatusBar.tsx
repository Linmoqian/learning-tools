import { useMemo } from 'react';
import { useStore } from '../lib/store';
import { DailyTone } from '../lib/types';

const TONE_CONFIG: Record<string, { icon: string; label: string; color: string }> = {
  [DailyTone.HIGH]: { icon: '⚡', label: '高效日', color: '#f0c040' },
  [DailyTone.NORMAL]: { icon: '☀️', label: '普通日', color: '#4a8fe7' },
  [DailyTone.LOW]: { icon: '🌙', label: '低负荷', color: '#9b59b6' },
  [DailyTone.REST]: { icon: '🏖️', label: '休息日', color: '#27ae60' },
};

export default function StatusBar() {
  const { data } = useStore();

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);
  const dailyState = data.dailyUserStates[today];
  const tone = dailyState?.dailyTone || DailyTone.NORMAL;
  const config = TONE_CONFIG[tone] || TONE_CONFIG[DailyTone.NORMAL];

  const doneToday = useMemo(
    () => data.tasks.filter(t => t.completed && t.updatedAt?.startsWith(today)).length,
    [data.tasks, today],
  );

  const streak = dailyState?.sleepEarlyStreak || 0;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '8px 16px',
        background: 'rgba(255,255,255,0.04)',
        borderRadius: 10,
        border: '1px solid rgba(255,255,255,0.06)',
        fontSize: 13,
      }}
    >
      <span style={{ color: config.color, fontWeight: 600 }}>
        {config.icon} {config.label}
      </span>
      <span style={{ color: '#6b6480' }}>|</span>
      <span style={{ color: '#a8a0b8' }}>
        ✅ 今日完成 {doneToday} 个任务
      </span>
      {streak > 0 && (
        <>
          <span style={{ color: '#6b6480' }}>|</span>
          <span style={{ color: '#f0c040' }}>
            🌙 {streak}天{' '.repeat(Math.min(Math.floor(streak / 3), 3))}
            {'⭐'.repeat(Math.min(Math.floor(streak / 3), 3))}
          </span>
        </>
      )}
    </div>
  );
}
