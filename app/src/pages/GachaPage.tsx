import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import { Clock, Sparkles, ListOrdered } from 'lucide-react';
import GachaButton from '../components/GachaButton';
import TaskCard from '../components/TaskCard';
import ChoiceDialog from '../components/ChoiceDialog';
import ReplaceDialog from '../components/ReplaceDialog';
import Timer from '../components/Timer';
import StatusBar from '../components/StatusBar';
import { useStore } from '../lib/store';
import {
  Task, GachaSessionContext, DrawChoiceResult,
  GACHA_POOL_NAMES,
} from '../lib/types';
import {
  getPoolForTime, filterByPool, getTopWeighted, planMultiDraw,
  createSessionContext, isDdlUrgent,
} from '../lib/algorithms';

export default function GachaPage() {
  const { dispatch, getAvailableTasks } = useStore();
  const pageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = pageRef.current;
    if (!el) return;
    const title = el.querySelector('h1');
    const content = el.querySelector('[data-gacha-content]');
    const tl = gsap.timeline();
    if (title) {
      tl.fromTo(title, { y: -20, opacity: 0, scale: 0.9 }, { y: 0, opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.7)' });
    }
    if (content) {
      tl.fromTo(content.children, { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.35, stagger: 0.07, ease: 'power2.out' }, '-=0.1');
    }
    return () => { tl.kill(); };
  }, []);

  const [minutes, setMinutes] = useState(25);
  const [sessionCtx] = useState<GachaSessionContext>(createSessionContext());
  const [drawResult, setDrawResult] = useState<DrawChoiceResult | null>(null);
  const [multiResults, setMultiResults] = useState<DrawChoiceResult[]>([]);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [showReplace, setShowReplace] = useState(false);
  const [replaceTaskId, setReplaceTaskId] = useState<number>(0);
  const [showTimer, setShowTimer] = useState(false);
  const [poolName, setPoolName] = useState('');

  const pool = getPoolForTime(minutes);

  const updatePoolHint = (m: number) => {
    const p = getPoolForTime(m);
    setPoolName(p ? GACHA_POOL_NAMES[p] || '' : '时间不足');
  };

  const handleSingleDraw = () => {
    if (!pool) return;
    const available = getAvailableTasks();
    const poolTasks = filterByPool(available, pool);
    if (!poolTasks.length) return;

    const choices = getTopWeighted(poolTasks, 3, 'medium', sessionCtx);
    if (!choices.length) return;

    setDrawResult({ pool, choices, slotIndex: 0, isUrgent: isDdlUrgent(choices[0]) });
    setMultiResults([]);
    setSelectedTask(null);
    setShowTimer(false);

    // Record draw
    dispatch({ type: 'RECORD_DRAW', taskId: choices[0].id });
  };

  const handleMultiDraw = () => {
    if (!pool) return;
    const plans = planMultiDraw(minutes);
    if (!plans.length) return;

    const available = getAvailableTasks();
    const results: DrawChoiceResult[] = [];

    for (const { pool: p, count } of plans) {
      const poolTasks = filterByPool(available, p);
      if (poolTasks.length) {
        const choices = getTopWeighted(poolTasks, Math.min(count * 2, 5), 'medium', sessionCtx);
        if (choices.length) {
          results.push({ pool: p, choices, slotIndex: results.length, isUrgent: isDdlUrgent(choices[0]) });
          dispatch({ type: 'RECORD_DRAW', taskId: choices[0].id });
        }
      }
    }

    setMultiResults(results);
    setDrawResult(null);
    setSelectedTask(null);
    setShowTimer(false);
  };

  const handleSelectTask = (task: Task) => {
    setSelectedTask(task);
    setDrawResult(null);
    setMultiResults([]);
    dispatch({ type: 'SET_CURRENT_TASK', id: task.id });
    dispatch({
      type: 'RECORD_GACHA',
      record: {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        poolName: pool || 'unknown',
        availableTime: minutes,
        taskId: task.id,
        accepted: true,
      },
    });
    setShowTimer(true);
  };

  const handleSkip = (originalTask: Task) => {
    setReplaceTaskId(originalTask.id);
    setShowReplace(true);
    setDrawResult(null);
  };

  const handleReplace = (reason: string) => {
    dispatch({ type: 'RECORD_REJECTION', entry: { id: Date.now(), taskId: replaceTaskId, reason, timestamp: new Date().toISOString() } });
    setShowReplace(false);
    handleSingleDraw();
  };

  const handleTimerComplete = () => {
    if (selectedTask) {
      dispatch({ type: 'COMPLETE_TASK', id: selectedTask.id });
      setSelectedTask(null);
      setShowTimer(false);
    }
  };

  const availableTasks = getAvailableTasks();
  const plans = pool ? planMultiDraw(minutes) : [];
  const planSummary = plans.map(p => `${p.count}×${GACHA_POOL_NAMES[p.pool]}`).join(' + ');

  return (
    <div ref={pageRef} style={{ padding: '24px 32px', height: '100%', display: 'flex', flexDirection: 'column', gap: 16, overflow: 'auto' }}>
      {/* Header */}
      <div>
        <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sparkles size={24} color="#f0c040" />
          <span className="gradient-text">任务抽卡系统</span>
        </h1>
        <StatusBar />
      </div>

      {/* Main content */}
      <div data-gacha-content style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24 }}>
        {/* Time input + draw button */}
        <div
          className="glass"
          style={{
            padding: '24px 32px',
            borderRadius: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 24,
            width: '100%',
            maxWidth: 640,
            justifyContent: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Clock size={20} color="#a8a0b8" />
            <span style={{ color: '#a8a0b8', fontSize: 14 }}>我有</span>
            <input
              type="number"
              value={minutes}
              onChange={e => {
                const m = Math.max(1, Math.min(480, parseInt(e.target.value) || 1));
                setMinutes(m);
                updatePoolHint(m);
              }}
              style={{
                width: 70,
                padding: '6px 10px',
                borderRadius: 8,
                border: '1px solid rgba(240,192,64,0.3)',
                background: 'rgba(240,192,64,0.05)',
                color: '#f0c040',
                fontSize: 20,
                fontWeight: 700,
                textAlign: 'center',
                outline: 'none',
              }}
            />
            <span style={{ color: '#a8a0b8', fontSize: 14 }}>分钟可用</span>
          </div>

          <div style={{ color: pool ? '#f0c040' : '#e74c3c', fontSize: 14, fontWeight: 600, minWidth: 100, textAlign: 'center' }}>
            → {poolName || '时间不足'}
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <GachaButton
              onClick={handleSingleDraw}
              disabled={!pool || !availableTasks.length}
              label="单抽"
            />
            {pool && minutes >= 15 && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleMultiDraw}
                disabled={!availableTasks.length}
                style={{
                  width: 100,
                  height: 100,
                  borderRadius: 20,
                  border: '2px solid rgba(240,192,64,0.3)',
                  background: 'linear-gradient(135deg, rgba(240,192,64,0.1), rgba(240,192,64,0.02))',
                  backdropFilter: 'blur(8px)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 2,
                  opacity: availableTasks.length ? 1 : 0.4,
                }}
              >
                <ListOrdered size={20} color="#f0c040" />
                <span style={{ fontSize: 14, fontWeight: 700, color: '#f0c040' }}>连抽</span>
                {planSummary && (
                  <span style={{ fontSize: 9, color: '#a8a0b8' }}>{planSummary}</span>
                )}
              </motion.button>
            )}
          </div>
        </div>

        {/* Prompt */}
        <p style={{ color: '#6b6480', fontSize: 13 }}>
          卡池中有 <strong style={{ color: '#f0c040' }}>{availableTasks.length}</strong> 个可用任务
        </p>

        {/* Timer */}
        {showTimer && selectedTask && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass"
            style={{
              padding: 24,
              borderRadius: 20,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 12,
              width: '100%',
              maxWidth: 360,
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600, color: '#f0e8da', textAlign: 'center' }}>
              {selectedTask.name}
            </div>
            <Timer
              initialMinutes={selectedTask.estimatedTime || 25}
              onComplete={handleTimerComplete}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button
                onClick={() => {
                  dispatch({ type: 'COMPLETE_TASK', id: selectedTask.id });
                  setSelectedTask(null);
                  setShowTimer(false);
                }}
                style={{
                  padding: '6px 16px',
                  borderRadius: 8,
                  border: 'none',
                  background: '#27ae60',
                  color: '#fff',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                ✅ 完成
              </button>
              <button
                onClick={() => {
                  dispatch({ type: 'SKIP_TASK', id: selectedTask.id });
                  setSelectedTask(null);
                  setShowTimer(false);
                }}
                style={{
                  padding: '6px 16px',
                  borderRadius: 8,
                  border: '1px solid rgba(255,255,255,0.15)',
                  background: 'none',
                  color: '#a8a0b8',
                  fontSize: 12,
                  cursor: 'pointer',
                }}
              >
                🔄 跳过
              </button>
            </div>
          </motion.div>
        )}

        {/* Draw Result - Single */}
        <AnimatePresence>
          {drawResult && (
            <ChoiceDialog
              key="choice"
              pool={drawResult.pool}
              choices={drawResult.choices}
              isUrgent={drawResult.isUrgent}
              onSelect={handleSelectTask}
              onSkip={() => handleSkip(drawResult.choices[0])}
              onClose={() => setDrawResult(null)}
            />
          )}
        </AnimatePresence>

        {/* Draw Result - Multi */}
        {multiResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{ width: '100%', maxWidth: 800 }}
          >
            <div style={{ fontSize: 14, color: '#a8a0b8', marginBottom: 12 }}>
              连抽方案：{planSummary}
            </div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center' }}>
              {multiResults.flatMap(r => r.choices.slice(0, 2)).map((task, i) => (
                <div key={`${task.id}-${i}`} style={{ textAlign: 'center' }}>
                  <TaskCard task={task} index={i} />
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleSelectTask(task)}
                    style={{
                      marginTop: 8,
                      padding: '6px 16px',
                      borderRadius: 8,
                      border: 'none',
                      background: 'linear-gradient(135deg, #f0c040, #c99f2e)',
                      color: '#0a0e1a',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    ▶ 开始
                  </motion.button>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Single result */}
        {selectedTask && !showTimer && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{ textAlign: 'center' }}
          >
            <TaskCard task={selectedTask} />
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setShowTimer(true);
                dispatch({ type: 'SET_CURRENT_TASK', id: selectedTask.id });
              }}
              style={{
                marginTop: 12,
                padding: '10px 32px',
                borderRadius: 10,
                border: 'none',
                background: 'linear-gradient(135deg, #27ae60, #1e8449)',
                color: '#fff',
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              ▶ 开始番茄钟
            </motion.button>
          </motion.div>
        )}
      </div>

      {/* Replace dialog */}
      <AnimatePresence>
        {showReplace && (
          <ReplaceDialog
            taskId={replaceTaskId}
            onReplace={handleReplace}
            onCancel={() => setShowReplace(false)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
