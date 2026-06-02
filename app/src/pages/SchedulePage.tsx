import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CalendarDays, ChevronLeft, ChevronRight, Settings2, Plus, X, Trash2 } from 'lucide-react';
import { useStore } from '../lib/store';
import { DEFAULT_SLOTS } from '../lib/types';
import { format, addDays, subDays, parseISO } from 'date-fns';

export default function SchedulePage() {
  const { data, dispatch } = useStore();
  const [currentDate, setCurrentDate] = useState(new Date().toISOString().slice(0, 10));
  const [showActivityManager, setShowActivityManager] = useState(false);
  const [newActivity, setNewActivity] = useState('');

  const dateObj = parseISO(currentDate);
  const dayOfWeek = dateObj.getDay();
  const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];

  // Get schedule items for current date
  const daySchedule = useMemo(() => {
    return data.scheduleItems.filter(s => s.date === currentDate);
  }, [data.scheduleItems, currentDate]);

  // Get weekly templates for this day of week
  const weeklyTemplates = useMemo(() => {
    return data.scheduleItems.filter(s => s.scheduleType === 'weekly' && s.dayOfWeek === dayOfWeek);
  }, [data.scheduleItems, dayOfWeek]);

  const getActivity = (slotId: string): string => {
    const item = daySchedule.find(s => s.slotId === slotId);
    if (item) return item.activity;
    const weekly = weeklyTemplates.find(s => s.slotId === slotId);
    return weekly?.activity || '无安排';
  };

  const setSlotActivity = (slotId: string, activity: string) => {
    dispatch({
      type: 'SET_SCHEDULE_ITEM',
      item: {
        date: currentDate,
        slotId,
        activity,
        notes: '',
        scheduleType: 'temporary',
        dayOfWeek,
      },
    });
  };

  const todayStr = new Date().toISOString().slice(0, 10);

  return (
    <div style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CalendarDays size={24} color="#f0c040" />
          <h1 className="page-title" style={{ margin: 0 }}>日程安排</h1>
        </div>
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowActivityManager(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 16px',
            borderRadius: 10,
            border: '1px solid rgba(155,89,182,0.3)',
            background: 'rgba(155,89,182,0.1)',
            color: '#9b59b6',
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          <Settings2 size={14} />
          管理活动
        </motion.button>
      </div>

      {/* Date navigation */}
      <div
        className="glass"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
          padding: '12px 24px',
          borderRadius: 14,
          marginBottom: 16,
        }}
      >
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setCurrentDate(subDays(dateObj, 1).toISOString().slice(0, 10))}
          style={{ background: 'none', border: 'none', color: '#a8a0b8', cursor: 'pointer' }}
        >
          <ChevronLeft size={20} />
        </motion.button>

        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#f0e8da' }}>
            {format(dateObj, 'M月d日')}
          </div>
          <div style={{ fontSize: 12, color: currentDate === todayStr ? '#f0c040' : '#6b6480' }}>
            {dayNames[dayOfWeek]}
            {currentDate === todayStr && ' · 今天'}
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setCurrentDate(addDays(dateObj, 1).toISOString().slice(0, 10))}
          style={{ background: 'none', border: 'none', color: '#a8a0b8', cursor: 'pointer' }}
        >
          <ChevronRight size={20} />
        </motion.button>
      </div>

      {/* Schedule slots */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {DEFAULT_SLOTS.map((slot, i) => {
          const activity = getActivity(slot.slotId);
          const isBusy = activity !== '无安排';
          const isWeekly = weeklyTemplates.some(s => s.slotId === slot.slotId);

          return (
            <motion.div
              key={slot.slotId}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 16px',
                borderRadius: 12,
                background: isBusy
                  ? isWeekly
                    ? 'rgba(74,143,231,0.1)'
                    : 'rgba(39,174,96,0.08)'
                  : 'rgba(255,255,255,0.03)',
                border: `1px solid ${isBusy
                  ? isWeekly
                    ? 'rgba(74,143,231,0.3)'
                    : 'rgba(39,174,96,0.2)'
                  : 'rgba(255,255,255,0.06)'
                }`,
              }}
            >
              {/* Time */}
              <div style={{ minWidth: 80, textAlign: 'center' }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#f0e8da' }}>{slot.slotName}</div>
                <div style={{ fontSize: 10, color: '#6b6480' }}>{slot.startTime}-{slot.endTime}</div>
              </div>

              {/* Indicator */}
              {isWeekly && <span style={{ color: '#4a8fe7', fontSize: 10 }}>🔵</span>}

              {/* Activity select */}
              <select
                value={activity}
                onChange={e => setSlotActivity(slot.slotId, e.target.value)}
                style={{
                  flex: 1,
                  padding: '6px 10px',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: 'rgba(255,255,255,0.05)',
                  color: isBusy ? '#f0e8da' : '#6b6480',
                  fontSize: 13,
                  outline: 'none',
                  cursor: 'pointer',
                }}
              >
                <option value="无安排">无安排</option>
                {data.activityOptions.filter(a => a !== '无安排').map(a => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
            </motion.div>
          );
        })}
      </div>

      {/* Activity Manager Modal */}
      <AnimatePresence>
        {showActivityManager && (
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
              zIndex: 100,
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
                width: 400,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h3 style={{ fontSize: 18, fontWeight: 700, color: '#f0e8da', margin: 0 }}>管理活动选项</h3>
                <button
                  onClick={() => setShowActivityManager(false)}
                  style={{ background: 'none', border: 'none', color: '#a8a0b8', cursor: 'pointer' }}
                >
                  <X size={20} />
                </button>
              </div>

              {/* Add new */}
              <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <input
                  value={newActivity}
                  onChange={e => setNewActivity(e.target.value)}
                  placeholder="输入新活动名称"
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(255,255,255,0.05)',
                    color: '#f0e8da',
                    fontSize: 13,
                    outline: 'none',
                  }}
                />
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    if (newActivity.trim()) {
                      dispatch({ type: 'ADD_ACTIVITY', activity: newActivity.trim() });
                      setNewActivity('');
                    }
                  }}
                  style={{
                    padding: '8px 16px',
                    borderRadius: 8,
                    border: 'none',
                    background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
                    color: '#0a0e1a',
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  <Plus size={16} />
                </motion.button>
              </div>

              {/* Activity list */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 300, overflow: 'auto' }}>
                {data.activityOptions.filter(a => a !== '无安排').map(activity => (
                  <div
                    key={activity}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      borderRadius: 8,
                      background: 'rgba(255,255,255,0.03)',
                    }}
                  >
                    <span style={{ color: '#f0e8da', fontSize: 13 }}>{activity}</span>
                    <button
                      onClick={() => dispatch({ type: 'DELETE_ACTIVITY', activity })}
                      style={{ background: 'none', border: 'none', color: '#e74c3c', cursor: 'pointer', padding: 2 }}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

