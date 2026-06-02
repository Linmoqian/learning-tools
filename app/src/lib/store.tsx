import React, { createContext, useContext, useReducer, useEffect, useCallback, useRef, useState } from 'react';
import {
  Task,
  AppData,
  DailyUserState,
  GachaRecord,
  ScheduleItem,
  TaskRejectionLog,
  TaskCompletionFeedback,
  AppSettings,
  DEFAULT_SLOTS,
  DEFAULT_SETTINGS,
} from './types';
import * as api from './api';
import { chainUnlock } from './algorithms';

const STORAGE_KEY = 'learning-tools-data';

function createInitialData(): AppData {
  return {
    tasks: [],
    tags: [],
    dailyUserStates: {},
    gachaRecords: [],
    rejectionLog: [],
    completionFeedback: [],
    scheduleItems: [],
    scheduleSlots: DEFAULT_SLOTS,
    activityOptions: ['无安排', '学习', '工作', '阅读', '运动', '休息'],
    nextTaskId: 1,
    currentTaskId: null,
    settings: DEFAULT_SETTINGS,
  };
}

function loadFromLocal(): AppData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      // Ensure missing fields for migration from older data
      if (!parsed.scheduleSlots) parsed.scheduleSlots = DEFAULT_SLOTS;
      if (!parsed.activityOptions || !parsed.activityOptions.length) {
        parsed.activityOptions = ['无安排', '学习', '工作', '阅读', '运动', '休息'];
      }
      if (!parsed.settings) parsed.settings = DEFAULT_SETTINGS;
      return parsed;
    }
  } catch { /* ignore */ }
  return createInitialData();
}

function saveToLocal(data: AppData) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* ignore */ }
}

// ===== 从后端加载全量数据 =====
async function loadFromBackend(): Promise<AppData | null> {
  try {
    const online = await api.checkBackend();
    if (!online) return null;

    const [tasks, tags, gachaRecords, rejectionLog, settings] = await Promise.all([
      api.fetchTasks(),
      api.fetchTags(),
      api.fetchGachaRecords(),
      api.fetchRejectionLog(),
      api.fetchSettings(),
    ]);

    const today = new Date().toISOString().slice(0, 10);
    const dailyState = await api.fetchDailyState(today).catch(() => null);

    const scheduleSlots = DEFAULT_SLOTS;
    const activities = await api.fetchActivities().catch(() => []);

    const dailyUserStates: Record<string, DailyUserState> = {};
    if (dailyState && dailyState.date) {
      dailyUserStates[dailyState.date] = dailyState;
    }

    const maxId = tasks.reduce((max, t) => Math.max(max, t.id ?? 0), 0);

    return {
      tasks,
      tags,
      dailyUserStates,
      gachaRecords,
      rejectionLog,
      completionFeedback: [],
      scheduleItems: [],
      scheduleSlots,
      activityOptions: activities.length > 0 ? activities : ['无安排', '学习', '工作', '阅读', '运动', '休息'],
      nextTaskId: maxId + 1,
      currentTaskId: null,
      settings,
    };
  } catch (e) {
    console.warn('后端加载失败，使用本地数据:', e);
    return null;
  }
}

// ===== Actions =====
type Action =
  | { type: 'LOAD' }
  | { type: 'HYDRATE'; data: AppData }
  | { type: 'ADD_TASK'; task: Task }
  | { type: 'UPDATE_TASK'; task: Task }
  | { type: 'DELETE_TASK'; id: number }
  | { type: 'SET_CURRENT_TASK'; id: number | null }
  | { type: 'COMPLETE_TASK'; id: number; feedback?: { energy: number; mood: number } }
  | { type: 'SKIP_TASK'; id: number }
  | { type: 'RECORD_DRAW'; taskId: number }
  | { type: 'RECORD_REJECTION'; entry: TaskRejectionLog }
  | { type: 'RECORD_GACHA'; record: GachaRecord }
  | { type: 'MOVE_TO_DISCARD'; id: number }
  | { type: 'MOVE_FROM_DISCARD'; id: number }
  | { type: 'RESET_DISCARD' }
  | { type: 'SET_DAILY_STATE'; state: DailyUserState }
  | { type: 'ADD_TAG'; tag: string }
  | { type: 'DELETE_TAG'; tag: string }
  | { type: 'ADD_ACTIVITY'; activity: string }
  | { type: 'DELETE_ACTIVITY'; activity: string }
  | { type: 'SET_SCHEDULE_ITEM'; item: ScheduleItem }
  | { type: 'RECORD_SLEEP'; date: string; bedTime: string; onTime: boolean }
  | { type: 'RESET_PERIODIC' }
  | { type: 'UPDATE_SETTINGS'; settings: AppSettings };

function reducer(state: AppData, action: Action): AppData {
  switch (action.type) {
    case 'LOAD':
      return loadFromLocal();

    case 'HYDRATE':
      return { ...action.data };

    case 'ADD_TASK': {
      const task = { ...action.task, id: state.nextTaskId };
      return {
        ...state,
        tasks: [...state.tasks, task],
        nextTaskId: state.nextTaskId + 1,
      };
    }

    case 'UPDATE_TASK':
      return {
        ...state,
        tasks: state.tasks.map(t => (t.id === action.task.id ? action.task : t)),
      };

    case 'DELETE_TASK':
      return {
        ...state,
        tasks: state.tasks.filter(t => t.id !== action.id),
      };

    case 'SET_CURRENT_TASK':
      return { ...state, currentTaskId: action.id };

    case 'COMPLETE_TASK': {
      const now = new Date().toISOString();
      const tasks = state.tasks.map(t => {
        if (t.id !== action.id) return t;
        return {
          ...t,
          completed: true,
          updatedAt: now,
          successRate: Math.min(1.0, t.successRate + 0.1),
        };
      });
      // 链式解锁依赖此任务的后置任务
      const unlocked = chainUnlock(tasks, action.id);
      const newState = { ...state, tasks: unlocked.tasks };
      if (unlocked.unlocked.length > 0) {
        console.info(`链式解锁: ${unlocked.unlocked.join(', ')}`);
      }
      if (action.feedback) {
        const fb: TaskCompletionFeedback = {
          id: Date.now(),
          taskId: action.id,
          energyAfter: action.feedback.energy,
          moodAfter: action.feedback.mood,
          timestamp: new Date().toISOString(),
        };
        newState.completionFeedback = [...state.completionFeedback, fb];
      }
      return newState;
    }

    case 'SKIP_TASK': {
      const tasks = state.tasks.map(t =>
        t.id === action.id
          ? { ...t, completed: true, updatedAt: new Date().toISOString() }
          : t,
      );
      return { ...state, tasks };
    }

    case 'RECORD_DRAW': {
      const now = new Date().toISOString();
      return {
        ...state,
        tasks: state.tasks.map(t =>
          t.id === action.taskId
            ? { ...t, drawCountToday: t.drawCountToday + 1, lastDrawnAt: now, updatedAt: now }
            : t,
        ),
      };
    }

    case 'RECORD_REJECTION':
      return {
        ...state,
        rejectionLog: [...state.rejectionLog, action.entry],
        tasks: state.tasks.map(t =>
          t.id === action.entry.taskId
            ? { ...t, refusalCount: t.refusalCount + 1 }
            : t,
        ),
      };

    case 'RECORD_GACHA':
      return {
        ...state,
        gachaRecords: [...state.gachaRecords, action.record],
      };

    case 'MOVE_TO_DISCARD':
      return {
        ...state,
        tasks: state.tasks.map(t =>
          t.id === action.id
            ? { ...t, inDiscardPile: true, updatedAt: new Date().toISOString() }
            : t,
        ),
      };

    case 'MOVE_FROM_DISCARD':
      return {
        ...state,
        tasks: state.tasks.map(t =>
          t.id === action.id
            ? { ...t, inDiscardPile: false, updatedAt: new Date().toISOString() }
            : t,
        ),
      };

    case 'RESET_DISCARD':
      return {
        ...state,
        tasks: state.tasks.map(t =>
          t.inDiscardPile ? { ...t, inDiscardPile: false, updatedAt: new Date().toISOString() } : t,
        ),
      };

    case 'SET_DAILY_STATE': {
      const map = { ...state.dailyUserStates };
      map[action.state.date] = action.state;
      return { ...state, dailyUserStates: map };
    }

    case 'ADD_TAG': {
      if (state.tags.includes(action.tag)) return state;
      return { ...state, tags: [...state.tags, action.tag] };
    }

    case 'DELETE_TAG':
      return { ...state, tags: state.tags.filter(t => t !== action.tag) };

    case 'ADD_ACTIVITY': {
      if (state.activityOptions.includes(action.activity)) return state;
      return { ...state, activityOptions: [...state.activityOptions, action.activity] };
    }

    case 'DELETE_ACTIVITY':
      return {
        ...state,
        activityOptions: state.activityOptions.filter(a => a !== action.activity),
      };

    case 'SET_SCHEDULE_ITEM': {
      const idx = state.scheduleItems.findIndex(
        s => s.date === action.item.date && s.slotId === action.item.slotId,
      );
      let items: ScheduleItem[];
      if (idx >= 0) {
        items = state.scheduleItems.map((s, i) => (i === idx ? action.item : s));
      } else {
        items = [...state.scheduleItems, action.item];
      }
      return { ...state, scheduleItems: items };
    }

    case 'RECORD_SLEEP': {
      const map = { ...state.dailyUserStates };
      const existing = map[action.date] || {
        date: action.date,
        dailyTone: 'normal',
        sleepEarlyStreak: 0,
      };
      map[action.date] = {
        ...existing,
        bedTime: action.bedTime,
        sleepEarlyStreak: action.onTime
          ? (existing.sleepEarlyStreak ?? 0) + 1
          : 0,
      };
      return { ...state, dailyUserStates: map };
    }

    case 'UPDATE_SETTINGS':
      return { ...state, settings: action.settings };

    case 'RESET_PERIODIC': {
      const now = new Date().toISOString();
      return {
        ...state,
        tasks: state.tasks.map(t => {
          let updated = { ...t, drawCountToday: 0 };
          if (t.repeatType === 'daily' && t.completed && t.inDiscardPile) {
            updated = { ...updated, completed: false, inDiscardPile: false, nextAvailableAt: undefined };
          }
          if (t.repeatType === 'weekly' && t.completed && t.nextAvailableAt && t.nextAvailableAt <= now) {
            updated = { ...updated, completed: false, inDiscardPile: false, nextAvailableAt: undefined };
          }
          return { ...updated, updatedAt: now };
        }),
      };
    }

    default:
      return state;
  }
}

// ===== 后端同步调度 =====
async function syncAction(action: Action): Promise<void> {
  try {
    switch (action.type) {
      case 'ADD_TASK':
        await api.createTask(action.task);
        break;
      case 'UPDATE_TASK':
        if (action.task.id != null) await api.updateTask(action.task.id, action.task);
        break;
      case 'DELETE_TASK':
        await api.deleteTask(action.id);
        break;
      case 'COMPLETE_TASK':
        await api.completeTask(
          action.id,
          action.feedback ? { energyAfter: action.feedback.energy, moodAfter: action.feedback.mood } : undefined,
        );
        break;
      case 'SKIP_TASK':
        await api.skipTask(action.id);
        break;
      case 'RECORD_DRAW':
        await api.recordDraw(action.taskId);
        break;
      case 'RECORD_REJECTION':
        await api.gachaReject(action.entry.taskId, action.entry.reason);
        break;
      case 'RECORD_GACHA':
        await api.gachaAccept(action.record.taskId!, action.record.poolName, action.record.availableTime);
        break;
      case 'MOVE_TO_DISCARD':
        await api.discardTask(action.id);
        break;
      case 'MOVE_FROM_DISCARD':
        await api.restoreTask(action.id);
        break;
      case 'RESET_DISCARD':
        await api.resetDiscard();
        break;
      case 'SET_DAILY_STATE':
        await api.setDailyState(action.state);
        break;
      case 'RECORD_SLEEP':
        await api.recordSleep(action.date, action.bedTime, action.onTime);
        break;
      case 'SET_SCHEDULE_ITEM':
        await api.setScheduleItem(action.item);
        break;
      case 'RESET_PERIODIC':
        await api.resetPeriodic();
        break;
      case 'UPDATE_SETTINGS':
        await api.updateSettings(action.settings);
        if (action.settings.backendUrl) {
          api.setBackendUrl(action.settings.backendUrl);
        }
        break;
      case 'ADD_TAG':
        await api.createTag(action.tag);
        break;
      case 'DELETE_TAG':
        await api.deleteTag(action.tag);
        break;
      case 'ADD_ACTIVITY':
        await api.createActivity(action.activity);
        break;
      case 'DELETE_ACTIVITY':
        await api.deleteActivity(action.activity);
        break;
      default:
        break;
    }
  } catch (e) {
    console.warn(`后端同步失败(${action.type}):`, e);
  }
}

// ===== Context =====
interface StoreContextType {
  data: AppData;
  dispatch: React.Dispatch<Action>;
  backendOnline: boolean;
  getAvailableTasks: () => Task[];
  getDiscardTasks: () => Task[];
  getTaskById: (id: number) => Task | undefined;
}

const StoreContext = createContext<StoreContextType | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [data, dispatch] = useReducer(reducer, null, createInitialData);
  const [backendOnline, setBackendOnline] = useState(false);
  const initialized = useRef(false);

  // 初始化：先加载本地，再尝试从后端同步
  useEffect(() => {
    if (initialized.current) return;
    initialized.current = true;

    const local = loadFromLocal();
    dispatch({ type: 'HYDRATE', data: local });

    // 尝试从后端加载
    loadFromBackend().then(backendData => {
      if (backendData) {
        dispatch({ type: 'HYDRATE', data: backendData });
        setBackendOnline(true);
        // 同步后端地址到 API 模块
        if (backendData.settings.backendUrl) {
          api.setBackendUrl(backendData.settings.backendUrl);
        }
      }
    });
  }, []);

  // 自动保存到 localStorage（降级方案）
  useEffect(() => {
    if (initialized.current) {
      saveToLocal(data);
    }
  }, [data]);

  // 统一 dispatch：更新本地状态 + 同步后端
  const dataRef = useRef(data);
  dataRef.current = data;

  const syncDispatch = useCallback((action: Action) => {
    dispatch(action);
    syncAction(action);
  }, []);

  // 定期检查周期任务重置
  useEffect(() => {
    dispatch({ type: 'RESET_PERIODIC' });
    const interval = setInterval(() => {
      dispatch({ type: 'RESET_PERIODIC' });
    }, 60_000);
    return () => clearInterval(interval);
  }, []);

  const getAvailableTasks = useCallback(() => {
    const now = new Date().toISOString();
    return data.tasks.filter(t =>
      !t.completed &&
      (!t.nextAvailableAt || t.nextAvailableAt <= now) &&
      !t.inDiscardPile &&
      t.isUnlocked &&
      t.taskProfile !== 'daily_habit',
    );
  }, [data.tasks]);

  const getDiscardTasks = useCallback(() => {
    return data.tasks.filter(t => t.inDiscardPile && !t.completed);
  }, [data.tasks]);

  const getTaskById = useCallback((id: number) => {
    return data.tasks.find(t => t.id === id);
  }, [data.tasks]);

  return (
    <StoreContext.Provider value={{
      data, dispatch: syncDispatch, backendOnline,
      getAvailableTasks, getDiscardTasks, getTaskById,
    }}>
      {children}
    </StoreContext.Provider>
  );
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore must be used within StoreProvider');
  return ctx;
}
