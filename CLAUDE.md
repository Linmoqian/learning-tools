# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

学习工具 monorepo，包含四个子项目：

| 子项目 | 技术栈 | 说明 |
|--------|--------|------|
| `app/` | Tauri v2 + React 18 + TypeScript + Vite | 桌面端学习工具（脚手架阶段） |
| `任务发布系统/` | Python + PySide6 + SQLite | 任务随机发布器（核心项目） |
| `任务发布系统/StateOS/` | Python + PyQt6 + SQLite | 实时状态管理系统 |
| `笔记处理系统/` | Python 脚本 + 批处理 | Markdown/维基链接笔记处理工具集 |

## 核心项目：任务发布系统

### 架构

```
任务发布系统/
├── main.py                         # PySide6 应用入口
├── src/
│   ├── models/
│   │   ├── database.py             # SQLite 数据库（版本迁移、CRUD）
│   │   └── task.py                 # Task 模型、枚举、序列化/反序列化
│   ├── services/
│   │   ├── task_service.py         # 加权随机算法、任务依赖/解锁链
│   │   ├── gacha_service.py       # 抽卡引擎（冷却、换牌、连抽规划）
│   │   ├── state_service.py       # 每日基调、能量曲线、早睡记录
│   │   ├── export_service.py      # 数据导出
│   │   └── ai_import_processor.py # AI分析结果导入
│   └── ui/
│       ├── main_window.py          # 主窗口（番茄钟、状态栏、任务卡片）
│       ├── gacha_window.py         # 抽卡界面（选择弹窗、卡面渲染）
│       ├── schedule_window.py      # 日程安排
│       ├── dependency_graph.py     # 任务依赖关系图
│       └── filter_dialog.py        # 任务过滤
├── data/
│   └── task_publisher.db           # SQLite 数据库文件
├── ai_exports/                     # AI 分析导出目录
├── ai_imports/                     # AI 分析导入目录
├── AI_assistant_prompt.md          # AI 分析提示词
└── 任务随机发布器构思.txt           # 设计文档
```

### 核心架构模式

**Service 层** 接收 Database 实例，所有业务逻辑集中在 services/：

```
Database → Service (接收 Database) → UI (接收 Service 或 Database)
```

- `database.py`：单例式初始化，`_init_tables()` 创建全部表，`_run_migrations()` 管理版本迁移（当前 v1.5）
- `Task` 模型：纯数据类，`to_dict()` / `from_dict()` / `from_row()` 三种序列化方式
- 数据库版本管理通过 `_meta` 表，迁移前自动备份到 `data/backup/`

### 业务逻辑要点

**加权随机算法** (task_service.py)：
```
最终权重 = 基础权重 × DDL紧急度 × 精力匹配 × 阻力系数 × 成功率 × 拒绝惩罚 × task_profile策略权重 × 冷却因子
```

**四类 TaskProfile**：
- `DAILY_HABIT`：每日习惯，策略权重强制 0（不参与抽卡）
- `WEEKLY_ROUTINE`：每周任务，越接近周末权重越高
- `DEADLINE_FLEXIBLE`：柔性截止，临近 DDL 权重递增
- `DEADLINE_PROGRESSIVE`：渐进式截止，固定权重

**抽卡流程** (gacha_service.py)：
- 单抽 → 返回 top-3 候选供用户选择
- 连抽 → 根据总时间自动规划（15-24min→碎片池, 25-89min→番茄池, 90+min→深度池+碎片）
- 换牌 → 记录拒绝理由，冷却被换任务
- 连抽规划引擎 `plan_multi_draw(total_minutes)` 控制时间分配

**依赖解锁链** (task_service.py)：
- `_chain_unlock()` 递归解锁所有满足前置条件且未完成的任务
- `detect_cycle()` DFS 检测循环依赖
- 跳过任务同样触发解锁

### 命令

```bash
# 启动任务发布系统
cd 任务发布系统 && python main.py

# 安装依赖
cd 任务发布系统 && pip install -r requirements.txt

# StateOS
cd 任务发布系统/StateOS && python main.py
```

## 子项目：Tauri app

`app/` 目前是 Tauri v2 + React 脚手架，只有一个 greet 示例。

```bash
cd app
npm install
npm run tauri dev    # 开发模式
npm run tauri build  # 构建
```

## 子项目：笔记处理系统

独立 Python 脚本集合，用于处理 Markdown 笔记文件的维基链接转换、知识点分析、链接清理等。每个脚本独立运行，无统一入口。

```bash
python 笔记处理系统/工具/check_links_v2.py
python 笔记处理系统/工具/convert_to_wikilinks.py
...
```

## 关键设计约束

- 数据库迁移使用 `_meta` 表版本号管理，迁移前自动备份
- Task 字段通过 `ALTER TABLE` + try-except 渐进式添加（`_add_legacy_columns()`）
- 周期任务通过 `repeat_type` 字段控制，每日重置 `draw_count_today`
- AI 工作流：UI 导出 JSON → 粘贴给 AI → AI 输出文件放入 `ai_imports/` → 重启自动导入
