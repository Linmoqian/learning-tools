import { Task, TaskProfile, GachaPool, GACHA_POOL_RANGES, GachaSessionContext } from './types';

// ===== Weighted Random Algorithm =====
export function calculateFullWeight(
  task: Task,
  currentEnergy: string,
  sessionContext?: GachaSessionContext,
): number {
  let w = 1.0;
  w *= calculatePriorityWeight(task);
  w *= calculateDeadlineUrgency(task);
  w *= calculateEnergyMatch(task, currentEnergy);
  w *= calculateResistanceFactor(task);
  w *= calculateSuccessRateFactor(task);
  w *= calculateRefusalPenalty(task);
  w *= calculateProfileStrategyWeight(task);
  if (sessionContext) w *= calculateCooldownFactor(task, sessionContext);
  return Math.max(0.01, w);
}

function calculatePriorityWeight(task: Task): number {
  return task.priority / 5.0;
}

function calculateDeadlineUrgency(task: Task): number {
  if (!task.deadline) return 1.0;
  const now = Date.now();
  const deadline = new Date(task.deadline).getTime();
  if (deadline <= now) return 3.0;
  const daysLeft = (deadline - now) / (1000 * 60 * 60 * 24);
  if (daysLeft <= 1) return 2.5;
  if (daysLeft <= 3) return 1.5;
  if (daysLeft <= 7) return 1.0 + (7.0 - daysLeft) * 0.1;
  return 0.5;
}

function calculateEnergyMatch(task: Task, currentEnergy: string): number {
  const score: Record<string, number> = { low: 0, medium: 1, high: 2 };
  const t = score[task.energyRequired] ?? 1;
  const c = score[currentEnergy] ?? 1;
  return Math.max(0.5, 1.5 - Math.abs(t - c) * 0.3);
}

function calculateResistanceFactor(task: Task): number {
  const m: Record<string, number> = { low: 1.0, medium: 0.8, high: 0.6 };
  return m[task.resistance] ?? 1.0;
}

function calculateSuccessRateFactor(task: Task): number {
  return 0.5 + task.successRate * 0.5;
}

function calculateRefusalPenalty(task: Task): number {
  return Math.max(0.3, 1.0 - task.refusalCount * 0.1);
}

function calculateProfileStrategyWeight(task: Task): number {
  const now = new Date();
  if (task.taskProfile === TaskProfile.DAILY_HABIT) return 0.0;
  if (task.taskProfile === TaskProfile.WEEKLY_ROUTINE) {
    const dow = now.getDay();
    if (dow <= 3) return 0.3;
    if (dow <= 5) return 1.5;
    return 3.0;
  }
  if (task.taskProfile === TaskProfile.DEADLINE_FLEXIBLE) {
    if (!task.deadline) return 1.0;
    const days = (new Date(task.deadline).getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    if (days > 7) return 0.5;
    if (days > 3) return 1.0;
    if (days > 1) return 1.5;
    return 2.5;
  }
  if (task.taskProfile === TaskProfile.DEADLINE_PROGRESSIVE) return 1.0;
  return 1.0;
}

function calculateCooldownFactor(task: Task, ctx: GachaSessionContext): number {
  if (ctx.lastDrawnTaskId != null && task.id === ctx.lastDrawnTaskId) return 0.0;
  let f = 1.0;
  if (ctx.lastDrawnCategory != null && task.category === ctx.lastDrawnCategory) f *= 0.3;
  const counts: Record<string, number> = {};
  for (const cat of ctx.categoryHistory) counts[cat] = (counts[cat] ?? 0) + 1;
  if ((counts[task.category] ?? 0) >= 2) f *= 0.5;
  if (task.drawCountToday >= 3) f *= 0.2;
  return f;
}

// ===== Weighted Selection =====
export function selectWeightedRandom(
  tasks: Task[],
  energy: string,
  ctx?: GachaSessionContext,
): Task | null {
  if (!tasks.length) return null;
  const weights = tasks.map(t => calculateFullWeight(t, energy, ctx));
  const total = weights.reduce((a, b) => a + b, 0);
  if (total <= 0) return tasks[Math.floor(Math.random() * tasks.length)];
  let r = Math.random() * total;
  for (let i = 0; i < tasks.length; i++) {
    r -= weights[i];
    if (r <= 0) return tasks[i];
  }
  return tasks[tasks.length - 1];
}

export function getTopWeighted(
  tasks: Task[],
  n: number,
  energy: string,
  ctx?: GachaSessionContext,
): Task[] {
  if (!tasks.length) return [];
  const weighted = tasks.map(t => ({ task: t, weight: calculateFullWeight(t, energy, ctx) }));
  weighted.sort((a, b) => b.weight - a.weight);
  return weighted.slice(0, n).map(w => w.task);
}

// ===== Gacha Planning =====
export function getPoolForTime(minutes: number): GachaPool | null {
  if (minutes < 5) return null;
  if (minutes < 15) return GachaPool.FRAGMENT;
  if (minutes < 45) return GachaPool.TOMATO;
  return GachaPool.DEEP;
}

export function planMultiDraw(totalMinutes: number): Array<{ pool: GachaPool; count: number }> {
  if (totalMinutes < 15) return [];
  if (totalMinutes < 25) {
    const n = Math.max(1, Math.floor(totalMinutes / 7));
    return [{ pool: GachaPool.FRAGMENT, count: n }];
  }
  if (totalMinutes < 90) {
    const n = Math.max(1, Math.min(Math.floor(totalMinutes / 25), 4));
    return [{ pool: GachaPool.TOMATO, count: n }];
  }
  const deep = Math.max(1, Math.min(Math.floor(totalMinutes / 50), 3));
  const remaining = totalMinutes - deep * 50;
  const plans: Array<{ pool: GachaPool; count: number }> = [{ pool: GachaPool.DEEP, count: deep }];
  if (remaining >= 25) plans.push({ pool: GachaPool.TOMATO, count: 1 });
  else if (remaining >= 7) plans.push({ pool: GachaPool.FRAGMENT, count: 1 });
  return plans;
}

export function filterByPool(tasks: Task[], pool: GachaPool): Task[] {
  const [lo, hi] = GACHA_POOL_RANGES[pool];
  const filtered = tasks.filter(t => t.estimatedTime >= lo && t.estimatedTime < hi);
  return filtered.length ? filtered : tasks;
}

export function isDdlUrgent(task: Task): boolean {
  if (task.taskProfile === TaskProfile.DEADLINE_PROGRESSIVE) return true;
  if (!task.deadline) return false;
  const days = (new Date(task.deadline).getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  return days <= 1;
}

// ===== Cycle Detection =====
export function detectCycle(
  tasks: Task[],
  taskId: number,
  proposedPrerequisiteIds: number[],
): boolean {
  if (!proposedPrerequisiteIds.length) return false;
  const taskMap = new Map(tasks.map(t => [t.id, t]));
  const visited = new Set<number>();
  function dfs(currentId: number): boolean {
    if (currentId === taskId) return true;
    if (visited.has(currentId)) return false;
    visited.add(currentId);
    const t = taskMap.get(currentId);
    if (!t) return false;
    for (const pid of t.prerequisiteIds) {
      if (dfs(pid)) return true;
    }
    return false;
  }
  for (const pid of proposedPrerequisiteIds) {
    if (dfs(pid)) return true;
  }
  return false;
}

// ===== Chain Unlock =====
export function chainUnlock(tasks: Task[], completedTaskId: number): string[] {
  const unlocked: string[] = [];
  const taskMap = new Map(tasks.map(t => [t.id, t]));

  function checkAllPrereqsDone(task: Task): boolean {
    return task.prerequisiteIds.every(pid => taskMap.get(pid)?.completed ?? false);
  }

  function unlock(taskId: number) {
    const dependents = tasks.filter(t => t.prerequisiteIds.includes(taskId));
    for (const dep of dependents) {
      if (!dep.completed && !dep.isUnlocked && checkAllPrereqsDone(dep)) {
        dep.isUnlocked = true;
        unlocked.push(dep.name);
        unlock(dep.id);
      }
    }
  }
  unlock(completedTaskId);
  return unlocked;
}

// ===== New Session Context =====
export function createSessionContext(): GachaSessionContext {
  return {
    lastDrawnTaskId: null,
    lastDrawnCategory: null,
    categoryHistory: [],
    replaceCount: 0,
    maxReplaceCount: 1,
    replaceUsed: false,
    replacedTaskId: null,
  };
}

// ===== Create default task =====
export function createDefaultTask(): Omit<Task, 'id'> {
  const now = new Date().toISOString();
  return {
    name: '',
    category: 'daily',
    description: undefined,
    estimatedTime: 25,
    preferredTime: undefined,
    deadline: undefined,
    resistance: 'medium',
    energyRequired: 'medium',
    rarity: 'common',
    priority: 5,
    successRate: 0,
    refusalCount: 0,
    isDaily: false,
    taskType: 'normal',
    repeatType: 'none',
    taskProfile: 'deadline_flexible',
    parentTaskId: undefined,
    groupId: undefined,
    lastCompletedAt: undefined,
    nextAvailableAt: undefined,
    lastDrawnAt: undefined,
    drawCountToday: 0,
    minPushTime: '20:00',
    inDiscardPile: false,
    completedCount: 0,
    tags: [],
    completed: false,
    difficulty: undefined,
    createdAt: now,
    updatedAt: now,
    prerequisiteIds: [],
    isUnlocked: true,
  };
}
