import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Trash2, RotateCcw } from 'lucide-react';
import TaskCard from '../components/TaskCard';
import { useStore } from '../lib/store';

export default function DiscardPage() {
  const { data, dispatch } = useStore();
  const [tagFilter, setTagFilter] = useState('');

  const discardTasks = useMemo(() => {
    return data.tasks.filter(t => t.inDiscardPile && !t.completed);
  }, [data.tasks]);

  const filtered = useMemo(() => {
    if (!tagFilter) return discardTasks;
    return discardTasks.filter(t => t.tags.includes(tagFilter));
  }, [discardTasks, tagFilter]);

  const allTags = useMemo(() => {
    const set = new Set<string>();
    discardTasks.forEach(t => t.tags.forEach(tag => set.add(tag)));
    return Array.from(set).sort();
  }, [discardTasks]);

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Trash2 size={24} color="#e74c3c" />
          <h1 className="page-title" style={{ margin: 0 }}>弃牌堆</h1>
          <span style={{ color: '#6b6480', fontSize: 13 }}>({discardTasks.length} 张卡)</span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => dispatch({ type: 'RESET_DISCARD' })}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 16px',
              borderRadius: 10,
              border: '1px solid rgba(240,192,64,0.3)',
              background: 'rgba(240,192,64,0.1)',
              color: '#f0c040',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RotateCcw size={14} />
            重置全部
          </motion.button>
        </div>
      </div>

      {/* Tag filter */}
      {allTags.length > 0 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
          <button
            onClick={() => setTagFilter('')}
            style={{
              padding: '4px 12px',
              borderRadius: 14,
              border: 'none',
              background: tagFilter === '' ? 'rgba(240,192,64,0.2)' : 'rgba(255,255,255,0.05)',
              color: tagFilter === '' ? '#f0c040' : '#a8a0b8',
              fontSize: 12,
              cursor: 'pointer',
            }}
          >
            全部
          </button>
          {allTags.map(tag => (
            <button
              key={tag}
              onClick={() => setTagFilter(tag)}
              style={{
                padding: '4px 12px',
                borderRadius: 14,
                border: 'none',
                background: tagFilter === tag ? 'rgba(240,192,64,0.2)' : 'rgba(255,255,255,0.05)',
                color: tagFilter === tag ? '#f0c040' : '#a8a0b8',
                fontSize: 12,
                cursor: 'pointer',
              }}
            >
              #{tag}
            </button>
          ))}
        </div>
      )}

      {/* Info */}
      <div
        style={{
          padding: '8px 16px',
          borderRadius: 8,
          background: 'rgba(39,174,96,0.08)',
          border: '1px solid rgba(39,174,96,0.2)',
          color: '#27ae60',
          fontSize: 12,
          marginBottom: 16,
        }}
      >
        💡 每日任务每天会自动回到抽牌堆 · 每周任务下周会自动回到抽牌堆
      </div>

      {/* Cards */}
      {filtered.length === 0 ? (
        <div style={{ color: '#6b6480', fontSize: 14, padding: 40, textAlign: 'center' }}>
          弃牌堆为空
        </div>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, justifyContent: 'center' }}>
          {filtered.map((task, i) => (
            <motion.div
              key={task.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.03 }}
              style={{ textAlign: 'center' }}
            >
              <TaskCard task={task} index={i} compact />
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => dispatch({ type: 'MOVE_FROM_DISCARD', id: task.id })}
                style={{
                  marginTop: 8,
                  padding: '6px 14px',
                  borderRadius: 8,
                  border: '1px solid rgba(240,192,64,0.3)',
                  background: 'rgba(240,192,64,0.1)',
                  color: '#f0c040',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                🎴 抓回抽牌堆
              </motion.button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
