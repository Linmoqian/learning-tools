// ===== Enums =====
export const TaskCategory = {
  DAILY: 'daily',
  WEEKLY: 'weekly',
  FLEXIBLE_DDL: 'flexible_ddl',
  ACCUMULATION: 'accumulation',
} as const;
export type TaskCategory = (typeof TaskCategory)[keyof typeof TaskCategory];

export const RepeatType = {
  NONE: 'none',
  SINGLE: 'single',
  DAILY: 'daily',
  WEEKLY: 'weekly',
  ACCUMULATION: 'accumulation',
} as const;
export type RepeatType = (typeof RepeatType)[keyof typeof RepeatType];

export const TaskProfile = {
  DAILY_HABIT: 'daily_habit',
  WEEKLY_ROUTINE: 'weekly_routine',
  DEADLINE_FLEXIBLE: 'deadline_flexible',
  DEADLINE_PROGRESSIVE: 'deadline_progressive',
} as const;
export type TaskProfile = (typeof TaskProfile)[keyof typeof TaskProfile];

export const Resistance = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const;
export type Resistance = (typeof Resistance)[keyof typeof Resistance];

export const EnergyRequired = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const;
export type EnergyRequired = (typeof EnergyRequired)[keyof typeof EnergyRequired];

export const DailyTone = {
  HIGH: 'high',
  NORMAL: 'normal',
  LOW: 'low',
  REST: 'rest',
} as const;
export type DailyTone = (typeof DailyTone)[keyof typeof DailyTone];

export const GachaPool = {
  FRAGMENT: 'fragment',
  TOMATO: 'tomato',
  DEEP: 'deep',
} as const;
export type GachaPool = (typeof GachaPool)[keyof typeof GachaPool];

// ===== Interfaces =====
export interface Task {
  id: number;
  name: string;
  category: string;
  description?: string;
  estimatedTime: number;
  preferredTime?: string;
  deadline?: string;
  resistance: string;
  energyRequired: string;
  rarity: string;
  priority: number;
  successRate: number;
  refusalCount: number;
  isDaily: boolean;
  taskType: string;
  repeatType: string;
  taskProfile: string;
  parentTaskId?: number;
  groupId?: string;
  lastCompletedAt?: string;
  nextAvailableAt?: string;
  lastDrawnAt?: string;
  drawCountToday: number;
  minPushTime: string;
  inDiscardPile: boolean;
  completedCount: number;
  tags: string[];
  completed: boolean;
  difficulty?: number;
  createdAt: string;
  updatedAt: string;
  prerequisiteIds: number[];
  isUnlocked: boolean;
}

export interface DailyUserState {
  date: string;
  dailyTone: string;
  energyMorning?: number;
  energyAfternoon?: number;
  energyEvening?: number;
  bedTime?: string;
  sleepEarlyStreak: number;
}

export interface GachaRecord {
  id: number;
  timestamp: string;
  poolName: string;
  availableTime: number;
  taskId: number;
  accepted: boolean;
  refusalReason?: string;
}

export interface TaskRejectionLog {
  id: number;
  taskId: number;
  reason: string;
  timestamp: string;
}

export interface TaskCompletionFeedback {
  id: number;
  taskId: number;
  energyAfter: number;
  moodAfter: number;
  timestamp: string;
}

export interface ScheduleSlot {
  slotId: string;
  slotName: string;
  startTime: string;
  endTime: string;
  displayOrder: number;
}

export interface ScheduleItem {
  date: string;
  slotId: string;
  activity: string;
  notes?: string;
  scheduleType: 'temporary' | 'weekly';
  dayOfWeek?: number;
}

export interface DrawChoiceResult {
  pool: GachaPool;
  choices: Task[];
  slotIndex: number;
  isUrgent: boolean;
}

export interface GachaSessionContext {
  lastDrawnTaskId: number | null;
  lastDrawnCategory: string | null;
  categoryHistory: string[];
  replaceCount: number;
  maxReplaceCount: number;
  replaceUsed: boolean;
  replacedTaskId: number | null;
}

// ===== Settings =====
export interface LLSettings {
  apiUrl: string;
  apiKey: string;
  modelName: string;
}

export interface MinerU {
  apiUrl: string;
  apiKey: string;
}

export interface ThemeSettings {
  primaryColor: string;
  primaryColorLight: string;
  primaryColorDark: string;
}

export interface AppSettings {
  llm: LLSettings;
  mineru: MinerU;
  theme: ThemeSettings;
}

export const DEFAULT_SETTINGS: AppSettings = {
  llm: { apiUrl: '', apiKey: '', modelName: 'gpt-4o' },
  mineru: { apiUrl: '', apiKey: '' },
  theme: {
    primaryColor: '#f0c040',
    primaryColorLight: '#fae8a0',
    primaryColorDark: '#c99f2e',
  },
};

// ===== Store Shape =====
export interface AppData {
  tasks: Task[];
  tags: string[];
  dailyUserStates: Record<string, DailyUserState>;
  gachaRecords: GachaRecord[];
  rejectionLog: TaskRejectionLog[];
  completionFeedback: TaskCompletionFeedback[];
  scheduleItems: ScheduleItem[];
  scheduleSlots: ScheduleSlot[];
  activityOptions: string[];
  nextTaskId: number;
  currentTaskId: number | null;
  settings: AppSettings;
}

// ===== Default Schedule Slots =====
export const DEFAULT_SLOTS: ScheduleSlot[] = [
  { slotId: 'morning1', slotName: '上午第一节', startTime: '08:00', endTime: '09:00', displayOrder: 1 },
  { slotId: 'morning2', slotName: '上午第二节', startTime: '09:00', endTime: '10:00', displayOrder: 2 },
  { slotId: 'morning3', slotName: '上午第三节', startTime: '10:00', endTime: '11:00', displayOrder: 3 },
  { slotId: 'morning4', slotName: '上午第四节', startTime: '11:00', endTime: '12:00', displayOrder: 4 },
  { slotId: 'noon', slotName: '午休', startTime: '12:00', endTime: '14:00', displayOrder: 5 },
  { slotId: 'afternoon1', slotName: '下午第一节', startTime: '14:00', endTime: '15:00', displayOrder: 6 },
  { slotId: 'afternoon2', slotName: '下午第二节', startTime: '15:00', endTime: '16:00', displayOrder: 7 },
  { slotId: 'afternoon3', slotName: '下午第三节', startTime: '16:00', endTime: '17:00', displayOrder: 8 },
  { slotId: 'afternoon4', slotName: '下午第四节', startTime: '17:00', endTime: '18:00', displayOrder: 9 },
  { slotId: 'evening', slotName: '晚自习', startTime: '18:30', endTime: '21:30', displayOrder: 10 },
];

// ===== Profile Colors =====
export const PROFILE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  [TaskProfile.DAILY_HABIT]: { bg: '#7f8c8d', border: '#95a5a6', text: '#ffffff' },
  [TaskProfile.WEEKLY_ROUTINE]: { bg: '#27ae60', border: '#2ecc71', text: '#ffffff' },
  [TaskProfile.DEADLINE_FLEXIBLE]: { bg: '#2980b9', border: '#3498db', text: '#ffffff' },
  [TaskProfile.DEADLINE_PROGRESSIVE]: { bg: '#e74c3c', border: '#c0392b', text: '#ffffff' },
};

export const GACHA_POOL_NAMES: Record<string, string> = {
  [GachaPool.FRAGMENT]: '碎片卡池',
  [GachaPool.TOMATO]: '番茄卡池',
  [GachaPool.DEEP]: '深度卡池',
};

export const GACHA_POOL_RANGES: Record<string, [number, number]> = {
  [GachaPool.FRAGMENT]: [0, 15],
  [GachaPool.TOMATO]: [15, 45],
  [GachaPool.DEEP]: [45, 999],
};
