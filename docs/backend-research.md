# 后端调研报告

> 调研时间：2026-06-02
> 范围：前端 `app/src/` + Python 后端 `任务发布系统/src/` + Rust mineru-service

---

## 目录

1. [现有架构总览](#1-现有架构总览)
2. [Python 后端架构模式](#2-python-后端架构模式)
3. [数据库 Schema 设计](#3-数据库-schema-设计)
4. [Service 层业务逻辑清单](#4-service-层业务逻辑清单)
5. [前端与 Python 后端差异分析](#5-前端与-python-后端差异分析)
6. [新后端实施建议](#6-新后端实施建议)

---

## 1. 现有架构总览

```
app/ (Tauri v2 + React 前端)
  ├── src/lib/              ← 前端数据层（localStorage）
  │   ├── types.ts          ← 全部数据模型
  │   ├── store.tsx         ← useReducer（可视为前端数据库接口）
  │   ├── algorithms.ts     ← 加权随机、连抽规划（TS 实现）
  │   └── knowledge.ts      ← 知识库分析算法（TS 实现）
  ├── src-tauri/src/agent/  ← Rust 独立实现（仅 Agent 模块）
  └── mineru-service/       ← Rust actix-web 独立服务（仅文档转换）

任务发布系统/ (Python PySide6 桌面应用)
  ├── src/models/
  │   ├── database.py       ← SQLite 层（CRUD + 版本迁移）
  │   └── task.py           ← Task 模型 + 序列化
  ├── src/services/
  │   ├── task_service.py   ← 加权随机算法
  │   ├── gacha_service.py  ← 抽卡引擎
  │   ├── state_service.py  ← 状态管理
  │   └── export_service.py ← 数据导出
  └── src/ui/               ← PySide6 UI（前端无关）
```

### 关键发现

| 模块 | 当前状态 | 建议 |
|------|---------|------|
| 任务 CRUD | 前端 localStorage + Python 端 SQLite 各有一套 | 统一为后端 REST |
| 加权随机算法 | `algorithms.ts` 和 `task_service.py` 各有一份实现 | **逻辑完全一致**，证明算法已稳定 |
| 抽卡引擎 | `GachaPage.tsx` 调用 `algorithms.ts` + `gacha_service.py` | 两套实现，可合并 |
| 知识库分析 | 仅前端 `knowledge.ts` 实现 | 后端新增 |
| AI Agent | 仅 Rust Tauri Command 实现 | 可迁移为 REST |
| 日程管理 | 前端 `SchedulePage.tsx` + localStorage | 后端新增 |
| 用户状态 | 前端 `store.tsx` + Python `state_service.py` | 统一 |

---

## 2. Python 后端架构模式

### 2.1 架构层次

```
Database (database.py) → Service (接收 Database 实例) → UI (接收 Service 或 Database)
```

### 2.2 数据库层特征

- 单例式初始化
- `_init_tables()` 创建全部表（21 张表）
- `_run_migrations()` 管理版本迁移（当前 v1.5）
- 迁移前自动备份到 `data/backup/`
- 字段通过 `ALTER TABLE` + try-except 渐进式添加
- 使用 `_meta` 表记录版本号

### 2.3 Service 层特征

| Service | 职责 | 关键方法数 |
|---------|------|-----------|
| TaskService | 任务 CRUD + 加权权重计算 + 链式解锁 + 循环检测 | 18 |
| GachaService | 抽卡流程 + 连抽规划 + 换牌 + 记录 | 16 |
| StateService | 每日状态 + 能量曲线 + 睡眠记录 | 12 |
| ExportService | 全量数据导出为 JSON | 8 |

### 2.4 数据库迁移策略

```
v1.0 (初始) → v1.5 (迁移):
  - tasks 表新增: task_profile, parent_task_id, group_id, last_drawn_at,
    draw_count_today, min_push_time, prerequisite_ids, is_unlocked
  - 新建: daily_user_state, task_rejection_log, task_completion_feedback
```

---

## 3. 数据库 Schema 设计

基于 Python 端 `database.py` 的 21 张表，结合前端 `types.ts` 数据模型，整理新后端需要的核心表：

### 3.1 tasks（任务主表）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| id | INTEGER PK | 自增主键 | `Task.id` |
| name | TEXT NOT NULL | 任务名称 | `Task.name` |
| category | TEXT | daily/weekly/flexible_ddl/accumulation | `Task.category` |
| task_type | TEXT | normal | `Task.taskType` |
| description | TEXT | 描述 | `Task.description` |
| estimated_time | INTEGER | 预估分钟 | `Task.estimatedTime` |
| preferred_time | TEXT | 偏好时间 | `Task.preferredTime` |
| deadline | TEXT | 截止时间 ISO | `Task.deadline` |
| resistance | TEXT | low/medium/high | `Task.resistance` |
| energy_required | TEXT | low/medium/high | `Task.energyRequired` |
| rarity | TEXT | common/uncommon/rare/epic/legendary | `Task.rarity` |
| priority | INTEGER | 1-10 | `Task.priority` |
| success_rate | REAL | 0.0-1.0 | `Task.successRate` |
| refusal_count | INTEGER | 拒绝次数 | `Task.refusalCount` |
| is_daily | BOOLEAN | 是否每日 | `Task.isDaily` |
| repeat_type | TEXT | none/single/daily/weekly/accumulation | `Task.repeatType` |
| task_profile | TEXT | daily_habit/weekly_routine/... | `Task.taskProfile` |
| completed | BOOLEAN | 是否完成 | `Task.completed` |
| in_discard_pile | BOOLEAN | 是否弃牌 | `Task.inDiscardPile` |
| completed_count | INTEGER | 完成次数 | `Task.completedCount` |
| draw_count_today | INTEGER | 今日抽到次数 | `Task.drawCountToday` |
| min_push_time | TEXT | 最小推送时间 20:00 | `Task.minPushTime` |
| last_drawn_at | TEXT | 最后抽出时间 | `Task.lastDrawnAt` |
| last_completed_at | TEXT | 最后完成时间 | `Task.lastCompletedAt` |
| next_available_at | TEXT | 下次可用时间 | `Task.nextAvailableAt` |
| prerequisite_ids | TEXT JSON | 前置任务 ID 列表 | `Task.prerequisiteIds` |
| is_unlocked | INTEGER | 是否解锁 | `Task.isUnlocked` |
| parent_task_id | INTEGER | 父任务 | `Task.parentTaskId` |
| group_id | TEXT | 分组 ID | `Task.groupId` |
| difficulty | INTEGER | 难度 | `Task.difficulty` |
| created_at | TEXT | 创建时间 | `Task.createdAt` |
| updated_at | TEXT | 更新时间 | `Task.updatedAt` |

关联表：`tags`、`task_tags`（多对多）

### 3.2 daily_user_state（每日状态）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| id | INTEGER PK | | |
| date | TEXT UNIQUE | 日期 YYYY-MM-DD | `DailyUserState.date` |
| daily_tone | TEXT | high/normal/low/rest | `DailyUserState.dailyTone` |
| energy_morning | INTEGER | 0-5 | `DailyUserState.energyMorning` |
| energy_afternoon | INTEGER | 0-5 | `DailyUserState.energyAfternoon` |
| energy_evening | INTEGER | 0-5 | `DailyUserState.energyEvening` |
| bed_time | TEXT | HH:MM | `DailyUserState.bedTime` |
| sleep_early_streak | INTEGER | 连续早睡天数 | `DailyUserState.sleepEarlyStreak` |

### 3.3 gacha_records（抽卡记录）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| id | INTEGER PK | | |
| timestamp | TEXT | 时间 | `GachaRecord.timestamp` |
| pool_name | TEXT | fragment/tomato/deep | `GachaRecord.poolName` |
| available_time | INTEGER | 可用分钟 | `GachaRecord.availableTime` |
| task_id | INTEGER | 任务 ID FK | `GachaRecord.taskId` |
| accepted | BOOLEAN | 是否接受 | `GachaRecord.accepted` |
| refusal_reason | TEXT | 拒绝原因 | `GachaRecord.refusalReason` |

### 3.4 task_rejection_log（拒绝记录）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| id | INTEGER PK | | |
| task_id | INTEGER | 任务 ID FK | |
| reason | TEXT | 原因 | |
| timestamp | TEXT | 时间 | |

### 3.5 task_completion_feedback（完成反馈）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| id | INTEGER PK | | |
| task_id | INTEGER | 任务 ID FK | |
| energy_after | INTEGER | 完成后精力 | |
| mood_after | INTEGER | 完成后心情 | |
| timestamp | TEXT | 时间 | |

### 3.6 schedule（日程）

| 字段 | 类型 | 说明 | 对应前端字段 |
|------|------|------|-------------|
| 使用 user_schedule (周模板) + daily_schedules (每日覆盖) | | | |

### 3.7 activities（活动选项）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | |
| name | TEXT UNIQUE | 活动名称 |

### 3.8 新增表（前端需要但 Python 后端没有）

| 表名 | 来源 | 说明 |
|------|------|------|
| notes | `knowledge.ts` Note | 知识库笔记 |
| knowledge_points | `knowledge.ts` KnowledgePoint | 知识点 |
| settings | `types.ts` AppSettings | 应用设置（JSON 存储） |

---

## 4. Service 层业务逻辑清单

### 4.1 加权随机算法（两份实现，逻辑一致）

- `algorithms.ts`（前端 TypeScript）
- `task_service.py`（Python 后端）

```
最终权重 = 基础权重(1.0)
  × priorityWeight(priority/5.0)
  × deadlineUrgency(无DDL→1.0, ≤1天→2.5, ≤3天→1.5)
  × energyMatch(匹配→1.5, 不匹配→0.5)
  × resistanceFactor(低→1.0, 中→0.8, 高→0.6)
  × successRateFactor(0.5 + rate×0.5)
  × refusalPenalty(max(0.3, 1.0 - refusalCount×0.1))
  × profileStrategyWeight(周五→3.0, DDL前→2.5)
  × cooldownFactor(同任务→0.0, 同类×0.3)
```

### 4.2 连抽规划（两份实现，逻辑一致）

| 时间 | Python/Algorithms 一致策略 |
|------|--------------------------|
| < 15 min | 不抽 |
| 15-24 min | 碎片池 × max(1, total/7) |
| 25-89 min | 番茄池 × max(1, min(total/25, 4)) |
| ≥ 90 min | 深度 × min(total/50, 3) + 剩余碎片/番茄 |

### 4.3 链式解锁

完成任务后递归解锁所有满足前置条件的依赖任务。DFS 实现，两份一致。

### 4.4 循环依赖检测

DFS 检测，两份一致。

### 4.5 周期任务重置

每日重置 `drawCountToday`。每日重复任务：`completed=false, inDiscardPile=false`。每周重复任务：检查 `nextAvailableAt`。

---

## 5. 前端与 Python 后端差异分析

### 5.1 数据字段命名差异（需映射）

| Python (snake_case) | TypeScript (camelCase) | 说明 |
|---------------------|----------------------|------|
| estimated_time | estimatedTime | |
| preferred_time | preferredTime | |
| energy_required | energyRequired | |
| success_rate | successRate | |
| refusal_count | refusalCount | |
| is_daily | isDaily | |
| task_type | taskType | |
| repeat_type | repeatType | |
| task_profile | taskProfile | |
| in_discard_pile | inDiscardPile | |
| completed_count | completedCount | |
| draw_count_today | drawCountToday | |
| min_push_time | minPushTime | |
| last_drawn_at | lastDrawnAt | |
| last_completed_at | lastCompletedAt | |
| next_available_at | nextAvailableAt | |
| prerequisite_ids | prerequisiteIds JavaScript | Python 存 JSON 字符串 |
| is_unlocked | isUnlocked | |

### 5.2 前端需要但 Python 后端没有的功能

| 功能 | 前端文件 | 建议后端实现方式 |
|------|---------|----------------|
| 知识库笔记 CRUD | `knowledge.ts` | 新建 notes 表 + REST |
| 知识点 CRUD | `knowledge.ts` | 新建 knowledge_points 表 + REST |
| 链接分析 | `knowledge.ts → analyzeLinks()` | 后端服务端计算 |
| 图谱数据 | `knowledge.ts → buildGraph()` | 后端构建返回 JSON |
| 科目统计分析 | `knowledge.ts → getSubjectStats()` | 后端聚合 |
| 全文搜索 | `knowledge.ts → searchItems()` | SQL LIKE / FTS |
| 文件解析 | `fileParser.ts` | 可选后端实现（MinerU 服务已覆盖） |
| AI Agent | `AgentPanel.tsx` + Runt Commands | 迁移为 REST |
| 设置持久化 | `store.tsx` `UPDATE_SETTINGS` | settings 表 |

### 5.3 Python 有但前端不需要迁移的表

| 表 | 说明 |
|----|------|
| time_currency | 时间货币（前端无对应概念） |
| task_milestones | 任务里程碑（前端未使用） |
| task_dependencies | 任务依赖关系（前端用 JSON 字段替代） |
| user_state | 通用状态记录（前端用 DailyUserState 替代） |
| user_health_profile | 健康档案 |
| user_profile | 用户档案 |
| task_completions | 完成明细 |
| user_states | 状态冗余表 |
| time_logs | 时间日志 |
| ai_analysis_imports | AI 分析导入 |
| rest_days | 休息日 |
| _meta | 版本管理 |

---

## 6. 新后端实施建议

### 6.1 推荐技术栈

| 层 | 推荐 | 理由 |
|----|------|------|
| 语言 | Rust 或 Python | Rust 性能好且与 Tauri 共享生态；Python 开发快 |
| 框架 | actix-web / FastAPI | 已有 mineru-service 使用 actix-web |
| 数据库 | SQLite (通过 `rusqlite` / `sqlx`) | 桌面应用无需独立数据库服务 |
| ORM | 手写 SQL（借鉴 Python 端模式） | 数据模型简单，ORM 反而增加复杂度 |

### 6.2 分阶段实施

**阶段一：核心 CRUD（任务 + 日程 + 状态）**
- tasks CRUD
- daily_user_state
- gacha_records / task_rejection_log
- schedule / activities

**阶段二：知识库**
- notes / knowledge_points CRUD
- 链接分析 / 图谱构建

**阶段三：AI Agent 迁移**
- 从 Tauri Command 迁移为 REST
- 统一 API Key 管理

### 6.3 关键决策点

| 决策 | 选项 | 建议 |
|------|------|------|
| 是否保留前端算法 | 两端各一份 / 后端计算 | 抽卡算法应放后端，前端只请求结果 |
| API Key 存储 | 文件 / 数据库加密 / 系统密钥链 | 数据库加密存储 |
| 文件解析 | 仅 MinerU / 后端也可解析 | MinerU 优先，后端做 fallback |
| 数据迁移 | 从 localStorage 导入 / 从 Python SQLite 导入 | 优先从 Python SQLite 导入 |

### 6.4 完整的后端服务列表

```
app/backend/                     ← 新后端项目
  ├── src/
  │   ├── main.rs                ← 入口 + Router
  │   ├── config.rs              ← 环境变量配置
  │   ├── db.rs                  ← 数据库初始化 + 迁移
  │   ├── models/                ← 数据模型 + 序列化
  │   │   ├── task.rs
  │   │   ├── schedule.rs
  │   │   ├── gacha.rs
  │   │   ├── knowledge.rs
  │   │   └── settings.rs
  │   ├── services/              ← 业务逻辑
  │   │   ├── task_service.rs    ← CRUD + 加权随机 + 链式解锁
  │   │   ├── gacha_service.rs   ← 抽卡 + 连抽规划
  │   │   ├── knowledge_service.rs ← 分析 + 图谱
  │   │   ├── state_service.rs   ← 每日状态
  │   │   └── agent_service.rs   ← AI Agent 代理
  │   ├── routes/                ← REST 路由处理
  │   │   ├── task_routes.rs
  │   │   ├── gacha_routes.rs
  │   │   ├── knowledge_routes.rs
  │   │   ├── schedule_routes.rs
  │   │   ├── state_routes.rs
  │   │   ├── agent_routes.rs
  │   │   └── settings_routes.rs
  │   └── middleware/            ← 中间件
  │       ├── cors.rs
  │       └── logging.rs
  ├── Cargo.toml
  └── .env
```

---

> 文档版本：v1.0
> 下一阶段：基于 API 文档 + 调研报告，实施后端开发
