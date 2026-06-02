import type { Task, DailyUserState, GachaRecord, TaskRejectionLog, ScheduleItem, ScheduleSlot, AppSettings } from './types';

const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8900';

let backendUrl = DEFAULT_BACKEND_URL;
let backendOnline = false;

export function setBackendUrl(url: string) {
  backendUrl = url;
  backendOnline = false;
}

export function getBackendUrl(): string {
  return backendUrl;
}

export function isBackendOnline(): boolean {
  return backendOnline;
}

// ===== 通用请求封装 =====
async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const resp = await fetch(`${backendUrl}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    signal: options?.signal ?? AbortSignal.timeout(10_000),
  });
  const json = await resp.json();
  if (!json.success) {
    throw new Error(json.error || `请求失败: ${resp.status}`);
  }
  return json.data as T;
}

// ===== 健康检查 =====
export async function checkBackend(): Promise<boolean> {
  try {
    await request<any>('/api/settings', { signal: AbortSignal.timeout(3000) });
    backendOnline = true;
    return true;
  } catch {
    backendOnline = false;
    return false;
  }
}

// ===== 任务 CRUD =====
export async function fetchTasks(search?: string, tag?: string): Promise<Task[]> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (tag) params.set('tag', tag);
  const qs = params.toString();
  return request<Task[]>(`/api/tasks${qs ? `?${qs}` : ''}`);
}

export async function createTask(task: Partial<Task>): Promise<Task> {
  return request<Task>('/api/tasks', {
    method: 'POST',
    body: JSON.stringify(task),
  });
}

export async function updateTask(id: number, task: Partial<Task>): Promise<Task> {
  return request<Task>(`/api/tasks/${id}`, {
    method: 'PUT',
    body: JSON.stringify(task),
  });
}

export async function deleteTask(id: number): Promise<boolean> {
  return request<boolean>(`/api/tasks/${id}`, { method: 'DELETE' });
}

export async function completeTask(id: number, feedback?: { energyAfter: number; moodAfter: number }): Promise<{ unlockedTaskNames: string[]; unlockedTaskIds: number[] }> {
  return request(`/api/tasks/${id}/complete`, {
    method: 'POST',
    body: JSON.stringify({ feedback }),
  });
}

export async function skipTask(id: number): Promise<boolean> {
  return request<boolean>(`/api/tasks/${id}/skip`, { method: 'POST' });
}

export async function recordDraw(id: number): Promise<boolean> {
  return request<boolean>(`/api/tasks/${id}/draw`, { method: 'POST' });
}

export async function discardTask(id: number): Promise<boolean> {
  return request<boolean>(`/api/tasks/${id}/discard`, { method: 'POST' });
}

export async function restoreTask(id: number): Promise<boolean> {
  return request<boolean>(`/api/tasks/${id}/restore`, { method: 'POST' });
}

export async function resetDiscard(): Promise<number> {
  return request<number>('/api/tasks/reset-discard', { method: 'POST' });
}

export async function resetPeriodic(): Promise<boolean> {
  return request<boolean>('/api/tasks/reset-periodic', { method: 'POST' });
}

export async function detectCycle(taskId: number, proposedPrerequisiteIds: number[]): Promise<{ hasCycle: boolean; cycleDescription: string }> {
  return request('/api/tasks/detect-cycle', {
    method: 'POST',
    body: JSON.stringify({ taskId, proposedPrerequisiteIds }),
  });
}

// ===== 标签 =====
export async function fetchTags(): Promise<string[]> {
  return request<string[]>('/api/tags');
}

export async function createTag(name: string): Promise<boolean> {
  return request<boolean>('/api/tags', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function deleteTag(name: string): Promise<boolean> {
  return request<boolean>(`/api/tags/${encodeURIComponent(name)}`, { method: 'DELETE' });
}

// ===== 抽卡 =====
export async function gachaDraw(pool: string, currentEnergy?: string, availableTaskIds?: number[]): Promise<{
  pool: string; choices: Task[]; slotIndex: number; isUrgent: boolean;
}> {
  return request('/api/gacha/draw', {
    method: 'POST',
    body: JSON.stringify({ pool, currentEnergy: currentEnergy || 'medium', availableTaskIds }),
  });
}

export async function gachaPlan(totalMinutes: number): Promise<{ plans: { pool: string; count: number }[]; suggestions: string[] }> {
  return request('/api/gacha/plan', {
    method: 'POST',
    body: JSON.stringify({ totalMinutes }),
  });
}

export async function gachaAccept(taskId: number, poolName: string, availableTime: number): Promise<boolean> {
  return request<boolean>('/api/gacha/accept', {
    method: 'POST',
    body: JSON.stringify({ taskId, poolName, availableTime }),
  });
}

export async function gachaReject(taskId: number, reason: string): Promise<boolean> {
  return request<boolean>('/api/gacha/reject', {
    method: 'POST',
    body: JSON.stringify({ taskId, reason }),
  });
}

export async function fetchGachaRecords(): Promise<GachaRecord[]> {
  return request<GachaRecord[]>('/api/gacha/records');
}

export async function fetchRejectionLog(): Promise<TaskRejectionLog[]> {
  return request<TaskRejectionLog[]>('/api/gacha/rejections');
}

// ===== 日程 =====
export async function fetchScheduleSlots(): Promise<ScheduleSlot[]> {
  return request<ScheduleSlot[]>('/api/schedule/slots');
}

export async function fetchDaySchedule(date: string): Promise<{
  date: string; items: ScheduleItem[]; weeklyTemplates: ScheduleItem[];
}> {
  return request(`/api/schedule/${date}`);
}

export async function setScheduleItem(item: ScheduleItem): Promise<boolean> {
  return request<boolean>('/api/schedule', {
    method: 'POST',
    body: JSON.stringify(item),
  });
}

export async function deleteScheduleItem(date: string, slotId: string): Promise<boolean> {
  return request<boolean>(`/api/schedule/${date}/${slotId}`, { method: 'DELETE' });
}

export async function fetchWeeklySchedule(dayOfWeek: number): Promise<ScheduleItem[]> {
  return request<ScheduleItem[]>(`/api/schedule/weekly/${dayOfWeek}`);
}

export async function fetchActivities(): Promise<string[]> {
  return request<string[]>('/api/activities');
}

export async function createActivity(name: string): Promise<boolean> {
  return request<boolean>('/api/activities', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function deleteActivity(name: string): Promise<boolean> {
  return request<boolean>(`/api/activities/${encodeURIComponent(name)}`, { method: 'DELETE' });
}

// ===== 每日状态 =====
export async function fetchDailyState(date: string): Promise<DailyUserState> {
  return request<DailyUserState>(`/api/daily/state/${date}`);
}

export async function setDailyState(state: { date: string; dailyTone?: string; energyMorning?: number; energyAfternoon?: number; energyEvening?: number }): Promise<boolean> {
  return request<boolean>('/api/daily/state', {
    method: 'POST',
    body: JSON.stringify(state),
  });
}

export async function recordSleep(date: string, bedTime: string, onTime: boolean): Promise<boolean> {
  return request<boolean>('/api/daily/sleep', {
    method: 'POST',
    body: JSON.stringify({ date, bedTime, onTime }),
  });
}

// ===== 设置 =====
export async function fetchSettings(): Promise<AppSettings> {
  return request<AppSettings>('/api/settings');
}

export async function updateSettings(settings: AppSettings): Promise<boolean> {
  return request<boolean>('/api/settings', {
    method: 'PUT',
    body: JSON.stringify(settings),
  });
}

export async function resetSettings(): Promise<boolean> {
  return request<boolean>('/api/settings/reset', { method: 'PUT' });
}
