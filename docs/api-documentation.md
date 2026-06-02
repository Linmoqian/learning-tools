# 学习工具 — 后端 API 文档

> 基于 `app/src/` 前端代码逆向生成的接口需求文档。所有接口遵循 RESTful 风格，使用 JSON 通信。

---

## 目录

1. [概述](#1-概述)
2. [基础约定](#2-基础约定)
3. [MinerU 文档转换](#3-mineru-文档转换)
4. [任务管理](#4-任务管理)
5. [抽卡（Gacha）](#5-抽卡gacha)
6. [知识库管理](#6-知识库管理)
7. [日程管理](#7-日程管理)
8. [用户状态](#8-用户状态)
9. [AI Agent](#9-ai-agent)
10. [设置](#10-设置)
11. [全局数据模型](#11-全局数据模型)

---

## 1. 概述

本项目是一个学习辅助桌面应用（Tauri v2 + React），包含任务管理、抽卡激励、知识库、AI Agent 等模块。当前前端数据通过 `useReducer` + `localStorage` 管理，后端为独立服务，负责数据的持久化与计算。

### 架构关系

```
React 前端 (app/src/)
    │
    ├── REST API ──→ 后端服务 (建议 Rust actix-web / Python FastAPI)
    │                     │
    │                     ├── PostgreSQL / SQLite (持久化)
    │                     └── MinerU API (文档转换代理)
    │
    └── MinerU 服务 (已存在: mineru-service/)
                        └── MinerU API (mineru.net)
```

### 前端页面路由 （`app/src/App.tsx`）

| 路由 | 页面 | 说明 |
|------|------|------|
| `/gacha` | GachaPage | 抽卡主页（核心交互） |
| `/tasks` | TasksPage | 任务 CRUD |
| `/knowledge` | KnowledgePage | 知识库浏览/图谱/分析/Agent |
| `/discard` | DiscardPage | 弃牌堆管理 |
| `/schedule` | SchedulePage | 日程安排 |
| `/settings` | SettingsPage | 全局设置 |

---

## 2. 基础约定

### 2.1 请求/响应格式

所有请求体为 `application/json`。响应格式统一为：

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

错误时：

```json
{
  "success": false,
  "data": null,
  "error": "错误描述信息"
}
```

### 2.2 日期格式

所有时间字段使用 ISO 8601 字符串（`2026-06-02T10:30:00.000Z`），日期字段使用 `YYYY-MM-DD`。

### 2.3 分页

列表接口支持分页：

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `page` | number | 1 | 页码 |
| `pageSize` | number | 20 | 每页数量 |

响应包含：

```json
{
  "success": true,
  "data": [...],
  "meta": {
    "total": 100,
    "page": 1,
    "pageSize": 20
  }
}
```

### 2.4 错误码

| HTTP 状态码 | 说明 |
|------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 3. MinerU 文档转换

已有独立 Rust 服务（`app/mineru-service/`），无需改动。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| POST | `/convert` | 上传文件并转换 |
| GET | `/images/{filename}` | 获取转换后图片 |

### 3.1 健康检查

```
GET /health
```

响应：

```json
{
  "status": "ok",
  "mineru": true
}
```

### 3.2 文件转换

```
POST /convert
Content-Type: multipart/form-data

Body: file=<二进制文件>
```

支持文件类型（`app/src/components/FileDropZone.tsx`）：`.pdf`, `.pptx`, `.ppt`, `.docx`, `.doc`, `.md`

响应（`app/src/lib/mineruClient.ts` → `MinerUResult`）：

```json
{
  "name": "文件名.pdf",
  "title": "文件名（不含扩展名）",
  "content": "Markdown 格式转换结果",
  "images": ["img_001.png", "img_002.png"]
}
```

错误响应：

```json
{
  "error": "转换失败描述"
}
```

### 3.3 图片获取

```
GET /images/{filename}
```

返回图片二进制（`image/png` 或 `image/jpeg`）。

---

## 4. 任务管理

对应页面：`TasksPage.tsx`
数据模型：`types.ts` → `Task`

### 4.1 任务对象

```typescript
interface Task {
  id: number;
  name: string;
  category: string;          // 'daily' | 'weekly' | 'flexible_ddl' | 'accumulation'
  description?: string;
  estimatedTime: number;      // 预估耗时（分钟），默认 25
  preferredTime?: string;     // 偏好时间段
  deadline?: string;          // ISO 8601
  resistance: string;         // 'low' | 'medium' | 'high'
  energyRequired: string;     // 'low' | 'medium' | 'high'
  rarity: string;             // 'common' | 'uncommon' | 'rare' | 'epic' | 'legendary'
  priority: number;           // 1-10，默认 5
  successRate: number;        // 0.0-1.0，默认 0
  refusalCount: number;
  isDaily: boolean;
  taskType: string;           // 'normal'
  repeatType: string;         // 'none' | 'single' | 'daily' | 'weekly' | 'accumulation'
  taskProfile: string;        // 'daily_habit' | 'weekly_routine' | 'deadline_flexible' | 'deadline_progressive'
  parentTaskId?: number;
  groupId?: string;
  lastCompletedAt?: string;
  nextAvailableAt?: string;
  lastDrawnAt?: string;
  drawCountToday: number;
  minPushTime: string;        // 默认 '20:00'
  inDiscardPile: boolean;
  completedCount: number;
  tags: string[];
  completed: boolean;
  difficulty?: number;
  createdAt: string;          // ISO 8601
  updatedAt: string;          // ISO 8601
  prerequisiteIds: number[];  // 前置任务 ID 列表
  isUnlocked: boolean;        // 前置任务全部完成时自动解锁
}
```

### 4.2 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tasks` | 获取任务列表 |
| POST | `/api/tasks` | 创建任务 |
| GET | `/api/tasks/:id` | 获取单个任务 |
| PUT | `/api/tasks/:id` | 更新任务 |
| DELETE | `/api/tasks/:id` | 删除任务 |
| POST | `/api/tasks/:id/complete` | 完成任务 |
| POST | `/api/tasks/:id/skip` | 跳过任务 |
| POST | `/api/tasks/:id/draw` | 记录抽卡次数 |
| POST | `/api/tasks/:id/discard` | 移入弃牌堆 |
| POST | `/api/tasks/:id/restore` | 从弃牌堆恢复 |
| POST | `/api/tasks/:id/restore` | 从弃牌堆恢复 |
| POST | `/api/tasks/reset-discard` | 清空弃牌堆 |
| POST | `/api/tasks/reset-periodic` | 重置周期任务 |
| POST | `/api/tasks/detect-cycle` | 检测循环依赖 |
| POST | `/api/tasks/:id/chain-unlock` | 递归解锁依赖链 |

#### 4.2.1 获取任务列表

```
GET /api/tasks
```

查询参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `search` | string | 搜索名称和标签 |
| `tag` | string | 按标签过滤 |
| `completed` | boolean | 筛选完成/未完成 |
| `inDiscardPile` | boolean | 是否在弃牌堆 |
| `subject` | string | 按科目过滤 |
| `page` | number | 页码 |
| `pageSize` | number | 每页数量 |

#### 4.2.2 创建任务

```
POST /api/tasks
```

请求体（`TasksPage.tsx` formData 结构）：

```json
{
  "name": "完成高数第二章习题",
  "description": "课后习题 1-10 题",
  "estimatedTime": 45,
  "deadline": "2026-06-10T23:59:00.000Z",
  "resistance": "medium",
  "energyRequired": "high",
  "priority": 7,
  "repeatType": "none",
  "taskProfile": "deadline_flexible",
  "tags": ["高数", "习题"],
  "prerequisiteIds": []
}
```

服务端自动补全字段（参考 `algorithms.ts` → `createDefaultTask()`）：

```json
{
  "id": "自动生成",
  "category": "daily",
  "rarity": "common",
  "successRate": 0,
  "refusalCount": 0,
  "isDaily": false,
  "taskType": "normal",
  "drawCountToday": 0,
  "minPushTime": "20:00",
  "inDiscardPile": false,
  "completedCount": 0,
  "completed": false,
  "isUnlocked": true,
  "createdAt": "2026-06-02T10:00:00.000Z",
  "updatedAt": "2026-06-02T10:00:00.000Z"
}
```

#### 4.2.3 完成任务

```
POST /api/tasks/:id/complete
```

请求体（可选）：

```json
{
  "feedback": {
    "energyAfter": 3,
    "moodAfter": 4
  }
}
```

服务端处理：
- 设置 `completed = true`
- 更新 `updatedAt`
- `successRate` 增加 0.1（上限 1.0）
- 若提供 feedback，创建 `TaskCompletionFeedback`
- 触发依赖链解锁（参考 `algorithms.ts` → `chainUnlock()`）

#### 4.2.4 跳过任务

```
POST /api/tasks/:id/skip
```

服务端：设置 `completed = true`，更新 `updatedAt`。

#### 4.2.5 记录抽卡次数

```
POST /api/tasks/:id/draw
```

服务端：`drawCountToday += 1`，更新 `lastDrawnAt` 和 `updatedAt`。

#### 4.2.6 移入弃牌堆

```
POST /api/tasks/:id/discard
```

服务端：设置 `inDiscardPile = true`，更新 `updatedAt`。

#### 4.2.7 从弃牌堆恢复

```
POST /api/tasks/:id/restore
```

服务端：设置 `inDiscardPile = false`，更新 `updatedAt`。

#### 4.2.8 清空弃牌堆

```
POST /api/tasks/reset-discard
```

服务端：将所有 `inDiscardPile = true` 的任务设为 `inDiscardPile = false`。

#### 4.2.9 重置周期任务

```
POST /api/tasks/reset-periodic
```

服务端逻辑（`store.tsx` `RESET_PERIODIC` action）：
- 所有任务 `drawCountToday = 0`
- 每日重复任务（`repeatType === 'daily'`）：`completed = false`, `inDiscardPile = false`, `nextAvailableAt = undefined`
- 每周重复任务（`repeatType === 'weekly'`）：若 `nextAvailableAt` 已过期，同上

#### 4.2.10 检测循环依赖

```
POST /api/tasks/detect-cycle
```

请求体（`algorithms.ts` → `detectCycle()`）：

```json
{
  "taskId": 5,
  "proposedPrerequisiteIds": [3, 7]
}
```

响应：

```json
{
  "hasCycle": true,
  "cycleDescription": "任务 5 → 任务 3 → 任务 7 → 任务 5"
}
```

算法：DFS 检查前置任务链是否引回自身。

#### 4.2.11 递归解锁依赖链

```
POST /api/tasks/:id/chain-unlock
```

当任务完成时，递归检查哪些依赖该任务的任务满足全部前置条件并自动解锁（`algorithms.ts` → `chainUnlock()`）。

响应：

```json
{
  "unlockedTaskNames": ["任务A", "任务B"],
  "unlockedTaskIds": [6, 8]
}
```

### 4.3 标记与活动选项

前端使用字符串标签列表（`store.tsx`）。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/tags` | 获取所有标签 |
| POST | `/api/tags` | 添加标签 |
| DELETE | `/api/tags/:tag` | 删除标签 |

---

## 5. 抽卡（Gacha）

对应页面：`GachaPage.tsx`、`ChoiceDialog.tsx`、`ReplaceDialog.tsx`
核心算法：`algorithms.ts`
数据模型：`types.ts` → `GachaRecord`、`DrawChoiceResult`、`GachaSessionContext`、`TaskRejectionLog`

### 5.1 数据对象

```typescript
interface GachaRecord {
  id: number;
  timestamp: string;      // ISO 8601
  poolName: string;       // 'fragment' | 'tomato' | 'deep'
  availableTime: number;  // 可用时间（分钟）
  taskId: number;
  accepted: boolean;
  refusalReason?: string;
}

interface TaskRejectionLog {
  id: number;
  taskId: number;
  reason: string;         // '时间不够' | '太难' | '不想做' | ...
  timestamp: string;
}

interface DrawChoiceResult {
  pool: string;           // GachaPool
  choices: Task[];        // top-3 候选
  slotIndex: number;      // 计划中的槽位索引
  isUrgent: boolean;       // 是否有紧急 DDL
}

interface GachaSessionContext {
  lastDrawnTaskId: number | null;
  lastDrawnCategory: string | null;
  categoryHistory: string[];
  replaceCount: number;
  maxReplaceCount: number;
  replaceUsed: boolean;
  replacedTaskId: number | null;
}
```

### 5.2 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/gacha/draw` | 单抽（加权随机） |
| POST | `/api/gacha/replace` | 换牌 |
| POST | `/api/gacha/plan` | 连抽规划 |
| POST | `/api/gacha/accept` | 接受抽卡结果 |
| POST | `/api/gacha/reject` | 拒绝任务并记录原因 |
| GET | `/api/gacha/records` | 获取抽卡历史 |
| GET | `/api/gacha/rejections` | 获取拒绝记录 |

#### 5.2.1 单抽

```
POST /api/gacha/draw
```

请求体：

```json
{
  "pool": "tomato",
  "currentEnergy": "medium",
  "availableTasks": [5, 8, 12],
  "sessionContext": {
    "lastDrawnTaskId": null,
    "lastDrawnCategory": null,
    "categoryHistory": [],
    "replaceCount": 0,
    "maxReplaceCount": 1,
    "replaceUsed": false,
    "replacedTaskId": null
  }
}
```

服务端加权随机逻辑（`algorithms.ts` → `getTopWeighted()`）：

```
最终权重 = 基础权重
  × priorityWeight (priority / 5.0)
  × deadlineUrgency (无 DDL=1.0, ≤1天=2.5, ≤3天=1.5)
  × energyMatch (匹配=1.5, 不匹配=0.5)
  × resistanceFactor (低=1.0, 中=0.8, 高=0.6)
  × successRateFactor (0.5 + rate * 0.5)
  × refusalPenalty (max(0.3, 1.0 - refusalCount * 0.1))
  × profileStrategyWeight (常量表)
  × cooldownFactor (最近抽过=0.0, 同类别=0.3)
```

响应（`DrawChoiceResult`）：

```json
{
  "pool": "tomato",
  "choices": [
    { /* Task 对象 - 权重最高 */ },
    { /* Task 对象 - 权重第二 */ },
    { /* Task 对象 - 权重第三 */ }
  ],
  "slotIndex": 0,
  "isUrgent": false,
  "sessionContext": {
    "lastDrawnTaskId": 5,
    "lastDrawnCategory": "daily",
    "categoryHistory": ["daily"],
    "replaceCount": 0,
    "maxReplaceCount": 1,
    "replaceUsed": false,
    "replacedTaskId": null
  }
}
```

#### 5.2.2 换牌

```
POST /api/gacha/replace
```

请求体：

```json
{
  "pool": "tomato",
  "replacedTaskId": 5,
  "currentEnergy": "medium",
  "availableTaskIds": [8, 12, 15, 20],
  "sessionContext": {
    "lastDrawnTaskId": 5,
    "lastDrawnCategory": "daily",
    "categoryHistory": ["daily"],
    "replaceCount": 0,
    "maxReplaceCount": 1,
    "replacedTaskId": null,
    "replaceUsed": false
  }
}
```

服务端处理：
- 被换任务进入冷却（`cooldownFactor = 0.0`）
- 重新用加权随机选 top-3
- `sessionContext.replaceCount += 1`

响应同 `/draw`。

#### 5.2.3 连抽规划

```
POST /api/gacha/plan
```

请求体：

```json
{
  "totalMinutes": 120
}
```

服务端逻辑（`algorithms.ts` → `planMultiDraw()`）：

| 时间范围 | 规划策略 |
|---------|---------|
| < 15 min | 不抽 |
| 15-24 min | 碎片池 × N（N = max(1, floor(total/7))） |
| 25-89 min | 番茄池 × N（N = max(1, min(floor(total/25), 4))） |
| ≥ 90 min | 深度池 × D + 剩余碎片/番茄 |

响应：

```json
{
  "plans": [
    { "pool": "deep", "count": 2 },
    { "pool": "fragment", "count": 1 }
  ],
  "suggestions": [
    "深度卡池 × 2（每段 50 分钟）",
    "碎片卡池 × 1（约 10 分钟）"
  ]
}
```

#### 5.2.4 接受抽卡结果

```
POST /api/gacha/accept
```

请求体：

```json
{
  "taskId": 5,
  "poolName": "tomato",
  "availableTime": 30
}
```

创建 `GachaRecord`（`accepted: true`）。触发 `RECORD_DRAW` 逻辑。

#### 5.2.5 拒绝任务

```
POST /api/gacha/reject
```

请求体：

```json
{
  "taskId": 5,
  "reason": "时间不够"
}
```

创建 `TaskRejectionLog`。任务 `refusalCount += 1`。被拒任务进入冷却。

#### 5.2.6 抽卡历史

```
GET /api/gacha/records?page=1&pageSize=20
GET /api/gacha/rejections?page=1&pageSize=20
```

### 5.3 卡池时间范围（`types.ts`）

| 池 | 时间范围（分钟） |
|----|----------------|
| FRAGMENT（碎片） | 0-15 |
| TOMATO（番茄） | 15-45 |
| DEEP（深度） | 45+ |

---

## 6. 知识库管理

对应页面：`KnowledgePage.tsx`
数据模型：`knowledge.ts`
组件：`AgentPanel.tsx`、`FileDropZone.tsx`、`KnowledgeGraph.tsx`、`KnowledgeGraph3D.tsx`

### 6.1 数据对象

```typescript
interface Note {
  id: string;            // 'note_1' | 'upload_1234567890_0'
  name: string;          // 文件名
  subject: string;       // 科目
  title: string;         // 显示标题
  wikiLinks: string[];   // 维基链接（知识点引用）
  content: string;       // Markdown 内容
  images?: string[];     // MinerU 转换后的图片列表
}

interface KnowledgePoint {
  id: string;
  name: string;
  subject: string;
  description: string;
  linkedFrom: string[];  // 引用该知识点的笔记 ID 列表
  relatedPoints: string[];// 相关知识点名称
}

interface LinkAnalysisResult {
  totalNotes: number;
  totalKnowledgePoints: number;
  totalLinks: number;
  validLinks: number;
  brokenLinks: number;
  bySubject: Record<string, {
    notes: number;
    knowledgePoints: number;
    links: number;
    valid: number;
    broken: number;
  }>;
  brokenDetails: LinkIssue[];
  missingReferences: string[];
  knowledgePointNames: string[];
}

interface LinkIssue {
  type: 'broken_link' | 'missing_reference';
  noteId: string;
  noteName: string;
  noteSubject: string;
  targetName: string;
}

interface GraphData {
  nodes: Array<{
    id: string;
    label: string;
    type: 'note' | 'knowledge';
    subject: string;
    radius: number;
  }>;
  edges: Array<{
    source: string;
    target: string;
  }>;
}
```

### 6.2 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/knowledge/notes` | 获取笔记列表 |
| POST | `/api/knowledge/notes` | 创建笔记（上传） |
| GET | `/api/knowledge/notes/:id` | 获取单个笔记 |
| PUT | `/api/knowledge/notes/:id` | 更新笔记 |
| DELETE | `/api/knowledge/notes/:id` | 删除笔记 |
| GET | `/api/knowledge/points` | 获取知识点列表 |
| POST | `/api/knowledge/points` | 创建知识点 |
| GET | `/api/knowledge/points/:id` | 获取单个知识点 |
| PUT | `/api/knowledge/points/:id` | 更新知识点 |
| DELETE | `/api/knowledge/points/:id` | 删除知识点 |
| GET | `/api/knowledge/analysis` | 链接分析 |
| GET | `/api/knowledge/graph` | 图谱数据 |
| GET | `/api/knowledge/subjects` | 科目统计 |
| POST | `/api/knowledge/search` | 搜索笔记和知识点 |

#### 6.2.1 创建笔记

```
POST /api/knowledge/notes
```

请求体（`knowledge.ts` → `NewNoteInput`）：

```json
{
  "name": "01-01_函数的概念.pdf",
  "title": "函数的概念与基本要素",
  "subject": "高数",
  "wikiLinks": ["函数的概念与基本要素", "数列的极限"],
  "content": "Markdown 格式内容...",
  "images": ["高数-001.png", "高数-002.png"]
}
```

#### 6.2.2 创建知识点

```
POST /api/knowledge/points
```

请求体：

```json
{
  "name": "函数的概念与基本要素",
  "subject": "高数",
  "description": "函数的定义、定义域、值域、对应法则",
  "relatedPoints": ["数列的极限"]
}
```

#### 6.2.3 链接分析

```
GET /api/knowledge/analysis
```

服务端逻辑（`knowledge.ts` → `analyzeLinks()`）：
- 遍历所有笔记的 `wikiLinks`
- 在知识点名称集合中查找匹配
- 统计总链接数、有效链接、断链、按科目分布
- 识别缺失的引用（笔记中引用了不存在的知识点）

响应：

```json
{
  "totalNotes": 18,
  "totalKnowledgePoints": 38,
  "totalLinks": 47,
  "validLinks": 42,
  "brokenLinks": 5,
  "bySubject": {
    "高数": { "notes": 4, "knowledgePoints": 10, "links": 12, "valid": 11, "broken": 1 }
  },
  "brokenDetails": [...],
  "missingReferences": ["缺失知识点A"],
  "knowledgePointNames": ["知识点1", "知识点2", ...]
}
```

#### 6.2.4 图谱数据

```
GET /api/knowledge/graph
```

服务端逻辑（`knowledge.ts` → `buildGraph()`）：
- 笔记节点（`type: 'note'`）+ 知识点节点（`type: 'knowledge'`）
- 边：笔记的 `wikiLinks` → 知识点

响应：

```json
{
  "nodes": [
    { "id": "note_1", "label": "函数的概念...", "type": "note", "subject": "高数", "radius": 18 },
    { "id": "kp_1", "label": "函数的概念...", "type": "knowledge", "subject": "高数", "radius": 14 }
  ],
  "edges": [
    { "source": "note_1", "target": "kp_1" }
  ]
}
```

#### 6.2.5 科目统计

```
GET /api/knowledge/subjects
```

响应（`knowledge.ts` → `SubjectStat`）：

```json
[
  {
    "name": "高数",
    "color": "#e74c3c",
    "noteCount": 4,
    "kpCount": 10,
    "linkCount": 12,
    "validCount": 11,
    "brokenCount": 1
  }
]
```

科目列表（`knowledge.ts`）：

| 科目 | 颜色 |
|------|------|
| 高数 | `#e74c3c` |
| 线代 | `#9b59b6` |
| 大物 | `#3498db` |
| 电子技术 | `#e67e22` |
| 计算机 | `#2ecc71` |
| 英语四级 | `#f1c40f` |

#### 6.2.6 搜索

```
POST /api/knowledge/search
```

请求体（`knowledge.ts` → `searchItems()`）：

```json
{
  "query": "极限",
  "subjectFilter": null
}
```

响应：

```json
[
  {
    "type": "note",
    "id": "note_1",
    "name": "数列的极限",
    "subject": "高数",
    "matchField": "标题/内容"
  },
  {
    "type": "knowledge",
    "id": "kp_2",
    "name": "数列的极限",
    "subject": "高数",
    "matchField": "名称/描述"
  }
]
```

### 6.3 文件解析（前端现有逻辑，后端可选实现）

前端 `fileParser.ts` 使用浏览器端库（`pdfjs-dist`、`mammoth`、`jszip`）解析文件。若后端要实现文件解析：

```
POST /api/knowledge/parse-file
Content-Type: multipart/form-data
```

响应：

```json
{
  "name": "document.pdf",
  "content": "提取的纯文本内容"
}
```

---

## 7. 日程管理

对应页面：`SchedulePage.tsx`
数据模型：`types.ts` → `ScheduleSlot`、`ScheduleItem`

### 7.1 数据对象

```typescript
interface ScheduleSlot {
  slotId: string;         // 'morning1' | 'morning2' | ... | 'evening'
  slotName: string;       // '上午第一节'
  startTime: string;      // '08:00'
  endTime: string;        // '09:00'
  displayOrder: number;
}

interface ScheduleItem {
  date: string;           // '2026-06-02'
  slotId: string;
  activity: string;       // '学习' | '无安排' | 自定义
  notes?: string;
  scheduleType: 'temporary' | 'weekly';
  dayOfWeek?: number;     // 0=周日, 6=周六
}
```

### 7.2 默认时段（`DEFAULT_SLOTS`）

| slotId | 名称 | 时间 | 序号 |
|--------|------|------|------|
| morning1 | 上午第一节 | 08:00-09:00 | 1 |
| morning2 | 上午第二节 | 09:00-10:00 | 2 |
| morning3 | 上午第三节 | 10:00-11:00 | 3 |
| morning4 | 上午第四节 | 11:00-12:00 | 4 |
| noon | 午休 | 12:00-14:00 | 5 |
| afternoon1 | 下午第一节 | 14:00-15:00 | 6 |
| afternoon2 | 下午第二节 | 15:00-16:00 | 7 |
| afternoon3 | 下午第三节 | 16:00-17:00 | 8 |
| afternoon4 | 下午第四节 | 17:00-18:00 | 9 |
| evening | 晚自习 | 18:30-21:30 | 10 |

### 7.3 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/schedule/slots` | 获取默认时段 |
| GET | `/api/schedule/:date` | 获取某天日程 |
| POST | `/api/schedule` | 设置日程项 |
| DELETE | `/api/schedule/:date/:slotId` | 删除日程项 |
| GET | `/api/schedule/weekly/:dayOfWeek` | 获取每周模板 |
| GET | `/api/activities` | 获取活动选项列表 |
| POST | `/api/activities` | 添加活动选项 |
| DELETE | `/api/activities/:name` | 删除活动选项 |

默认活动选项（`store.tsx`）：

```
['无安排', '学习', '工作', '阅读', '运动', '休息']
```

#### 7.3.1 获取某天日程

```
GET /api/schedule/:date
```

路径参数：`date` 格式为 `YYYY-MM-DD`。

响应：

```json
{
  "date": "2026-06-02",
  "items": [
    {
      "slotId": "morning1",
      "activity": "高数复习",
      "notes": "第二章习题",
      "scheduleType": "temporary",
      "dayOfWeek": 2
    }
  ],
  "weeklyTemplates": [
    {
      "slotId": "morning2",
      "activity": "英语听力",
      "notes": "",
      "scheduleType": "weekly",
      "dayOfWeek": 2
    }
  ]
}
```

#### 7.3.2 设置日程项

```
POST /api/schedule
```

请求体：

```json
{
  "date": "2026-06-02",
  "slotId": "morning1",
  "activity": "高数复习",
  "notes": "第二章习题",
  "scheduleType": "temporary",
  "dayOfWeek": 2
}
```

---

## 8. 用户状态

对应组件：`StatusBar.tsx`、状态栏和每日基调系统。
数据模型：`types.ts` → `DailyUserState`

### 8.1 数据对象

```typescript
interface DailyUserState {
  date: string;                  // '2026-06-02'
  dailyTone: string;             // 'high' | 'normal' | 'low' | 'rest'
  energyMorning?: number;        // 0-5
  energyAfternoon?: number;      // 0-5
  energyEvening?: number;        // 0-5
  bedTime?: string;              // '23:00'
  sleepEarlyStreak: number;      // 连续早睡天数
}
```

### 8.2 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/daily/state/:date` | 获取某天状态 |
| POST | `/api/daily/state` | 设置每日状态 |
| POST | `/api/daily/sleep` | 记录睡眠 |

#### 8.2.1 设置每日状态

```
POST /api/daily/state
```

请求体：

```json
{
  "date": "2026-06-02",
  "dailyTone": "normal",
  "energyMorning": 3,
  "energyAfternoon": 4,
  "energyEvening": 2
}
```

#### 8.2.2 记录睡眠

```
POST /api/daily/sleep
```

请求体（`store.tsx` `RECORD_SLEEP`）：

```json
{
  "date": "2026-06-02",
  "bedTime": "23:00",
  "onTime": true
}
```

服务端逻辑：
- 记录 `bedTime`
- 若 `onTime === true`：`sleepEarlyStreak` 递增
- 若 `onTime === false`：`sleepEarlyStreak` 重置为 0

---

## 9. AI Agent

对应组件：`AgentPanel.tsx`
当前实现：Tauri Command（Rust 侧），建议迁移为独立 REST 接口。
数据模型：`agent/types.ts`

### 9.1 数据对象

```typescript
type AgentType = 'note_organizer' | 'knowledge_extractor'
               | 'structure_reviewer' | 'content_reviewer' | 'knowledge_qa';

type AIProvider = 'claude' | 'openai';

interface RunAgentRequest {
  agentType: AgentType;
  noteContent: string;
  provider?: AIProvider;
  model?: string;
}

interface AgentResult {
  content: string;
  model: string;
  provider: AIProvider;
}

type ApiKeyStatus = Record<AIProvider, boolean>;  // { claude: boolean, openai: boolean }
```

### 9.2 Agent 类型

| AgentType | 标签 | 说明 |
|-----------|------|------|
| `note_organizer` | 笔记整理 | 结构化整理、修正错别字、补充关键概念 |
| `knowledge_extractor` | 知识点整理 | 提取核心知识点，建立关联关系 |
| `structure_reviewer` | 结构审查 | 审查章节结构和逻辑层次 |
| `content_reviewer` | 内容审查 | 审查内容准确性和完整性 |
| `knowledge_qa` | 知识问答 | 基于知识库回答问题 |

### 9.3 Prompt 模板

每个 Agent 有对应的 System Prompt（`prompts.rs`），输出要求为 JSON 格式：

**note_organizer 输出格式：**

```json
{
  "title": "整理后的标题",
  "summary": "50字以内摘要",
  "content": "整理后的 Markdown",
  "changes": ["修正了 X 处错别字"]
}
```

**knowledge_extractor 输出格式：**

```json
{
  "knowledgePoints": [
    {
      "name": "知识点名称",
      "description": "50-100字说明",
      "subject": "所属学科",
      "prerequisites": ["前置知识点"],
      "successors": ["后置知识点"],
      "relatedPoints": ["相关知识点"]
    }
  ],
  "summary": "总体说明",
  "suggestedTags": ["标签1"]
}
```

**structure_reviewer 输出格式：**

```json
{
  "overallScore": 85,
  "structureMap": [
    {
      "section": "章节标题",
      "level": 1,
      "assessment": "合理 | 偏短 | 偏长 | 冗余",
      "suggestion": "建议"
    }
  ],
  "issues": [
    {
      "type": "missing_section | redundant_content | logic_gap | imbalance",
      "severity": "critical | major | minor",
      "description": "问题描述",
      "suggestion": "改进建议"
    }
  ],
  "summary": "总体评价"
}
```

**content_reviewer 输出格式：**

```json
{
  "overallScore": 85,
  "accuracy": {
    "score": 90,
    "errors": [
      {
        "type": "concept_error | formula_error | expression_issue",
        "severity": "critical | major | minor",
        "description": "问题描述",
        "correction": "正确表述"
      }
    ]
  },
  "completeness": { "score": 80, "missingPoints": [] },
  "depth": { "score": 85, "assessment": "评价", "suggestions": [] },
  "summary": "总体评价"
}
```

**knowledge_qa 输出格式：**

```json
{
  "answer": "Markdown 格式回答",
  "sources": ["引用的笔记标题"],
  "confidence": "high | medium | low",
  "followUpSuggestions": ["追问建议"]
}
```

### 9.4 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/run` | 运行 Agent |
| GET | `/api/agent/key-status` | 获取 API Key 状态 |
| POST | `/api/agent/save-key` | 保存 API Key |

#### 9.4.1 运行 Agent

```
POST /api/agent/run
```

请求体：

```json
{
  "agentType": "note_organizer",
  "noteContent": "笔记的完整内容...",
  "provider": "claude",
  "model": "claude-sonnet-4-20250514"
}
```

服务端流程（参考 `commands.rs` + `api_client.rs`）：
1. 根据 `agentType` 获取对应 System Prompt
2. 从存储读取对应 Provider 的 API Key
3. 调用对应 API（Claude Messages API / OpenAI Chat Completions API）
4. 返回原始响应

响应：

```json
{
  "content": "Agent 返回的原始文本（JSON 或 Markdown）",
  "model": "claude-sonnet-4-20250514",
  "provider": "claude"
}
```

#### 9.4.2 API Key 管理

```
GET /api/agent/key-status
```

响应：

```json
{
  "claude": true,
  "openai": false
}
```

```
POST /api/agent/save-key
```

请求体：

```json
{
  "provider": "claude",
  "key": "sk-ant-xxxxxxxxxxxx"
}
```

API Key 应加密存储，密钥文件位于应用数据目录下的 `api_keys.json`。

#### 9.4.3 知识问答上下文构建

当前端使用 `knowledge_qa` 时，前端会先搜索相关笔记和知识点（`AgentPanel.tsx` → `buildQaContext()`）。

可选后端实现：

```
POST /api/agent/qa-context
```

请求体：

```json
{
  "question": "什么是数列的极限？"
}
```

响应：

```json
{
  "context": "知识库上下文文本（包含相关笔记和知识点摘要）",
  "matchedNotes": ["note_1"],
  "matchedKnowledgePoints": ["kp_2"]
}
```

---

## 10. 设置

对应页面：`SettingsPage.tsx`
数据模型：`types.ts` → `AppSettings`

### 10.1 数据对象

```typescript
interface AppSettings {
  llm: {
    apiUrl: string;      // LLM API 地址
    apiKey: string;      // LLM API Key
    modelName: string;   // 模型名称，默认 'gpt-4o'
  };
  mineru: {
    apiUrl: string;      // MinerU 服务地址
    apiKey: string;      // MinerU API Key
  };
  theme: {
    primaryColor: string;      // 主色，默认 '#f5e6a0'
    primaryColorLight: string; // 浅色变体，默认 '#fdf6d4'
    primaryColorDark: string;  // 深色变体，默认 '#d4c06a'
    themeMode: 'light' | 'dark';
  };
}
```

### 10.2 接口列表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings` | 获取全部设置 |
| PUT | `/api/settings` | 更新设置 |
| PUT | `/api/settings/reset` | 恢复默认设置 |

#### 10.2.1 获取设置

```
GET /api/settings
```

响应：完整的 `AppSettings` 对象。

#### 10.2.2 更新设置

```
PUT /api/settings
```

请求体：完整的 `AppSettings` 对象。

```json
{
  "llm": {
    "apiUrl": "https://api.openai.com/v1",
    "apiKey": "sk-...",
    "modelName": "gpt-4o"
  },
  "mineru": {
    "apiUrl": "http://127.0.0.1:8899",
    "apiKey": ""
  },
  "theme": {
    "primaryColor": "#f5e6a0",
    "primaryColorLight": "#fdf6d4",
    "primaryColorDark": "#d4c06a",
    "themeMode": "light"
  }
}
```

---

## 11. 全局数据模型

### 11.1 枚举常量

| 枚举 | 值 |
|------|-----|
| `TaskCategory` | `daily` / `weekly` / `flexible_ddl` / `accumulation` |
| `RepeatType` | `none` / `single` / `daily` / `weekly` / `accumulation` |
| `TaskProfile` | `daily_habit` / `weekly_routine` / `deadline_flexible` / `deadline_progressive` |
| `Resistance` | `low` / `medium` / `high` |
| `EnergyRequired` | `low` / `medium` / `high` |
| `DailyTone` | `high` / `normal` / `low` / `rest` |
| `GachaPool` | `fragment` / `tomato` / `deep` |
| `AgentType` | `note_organizer` / `knowledge_extractor` / `structure_reviewer` / `content_reviewer` / `knowledge_qa` |
| `AIProvider` | `claude` / `openai` |

### 11.2 前端页面 → API 映射总表

| 页面 | 文件 | 使用的 API |
|------|------|-----------|
| GachaPage | `GachaPage.tsx` + `ChoiceDialog.tsx` + `ReplaceDialog.tsx` | 任务获取、抽卡绘制、记录 |
| TasksPage | `TasksPage.tsx` + `TaskForm.tsx` + `TaskCard.tsx` | 任务 CRUD、循环检测 |
| KnowledgePage | `KnowledgePage.tsx` + `KnowledgeGraph.tsx` + `KnowledgeGraph3D.tsx` + `FileDropZone.tsx` + `AgentPanel.tsx` | 笔记 CRUD、知识点 CRUD、图谱、分析、Agent |
| DiscardPage | `DiscardPage.tsx` | 弃牌堆管理 |
| SchedulePage | `SchedulePage.tsx` | 日程 CRUD、周模板 |
| SettingsPage | `SettingsPage.tsx` | 设置 CRUD |
| （状态栏） | `StatusBar.tsx` | 每日状态、睡眠记录 |
| （全局） | `App.tsx` | 设置读取、主题应用 |

### 11.3 文件结构参考

```
app/src-tauri/src/agent/     ← AI Agent 当前实现（Tauri Command）
  ├── mod.rs
  ├── commands.rs            ← run_agent, get_api_key_status, save_api_key
  ├── api_client.rs          ← call_claude(), call_openai()
  ├── key_manager.rs         ← API Key 加密存储
  └── prompts.rs             ← 5 个 System Prompt

app/src/lib/
  ├── types.ts               ← 全部 TypeScript 数据模型
  ├── store.tsx              ← useReducer 状态管理（可视为前端数据库接口）
  ├── algorithms.ts          ← 加权随机、连抽规划、循环检测、链式解锁
  ├── knowledge.ts           ← 知识库数据构建、链接分析、搜索
  ├── mineruClient.ts        ← MinerU 服务 REST 客户端
  ├── fileParser.ts          ← 客户端文件解析（pdfjs/mammoth/jszip）
  └── gsap-animations.ts     ← GSAP 动画钩子
```

---

> 文档版本：v1.0
> 基于前端代码：`app/src/`（2026-06-02）
> 后续迭代：建议将 Tauri Commands（Agent 模块）迁移为独立 REST 服务，与主后端统一。
