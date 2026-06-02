# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

桌面学习工具，主体是 Tauri v2 + React 前端 + Rust actix-web 后端。Python 项目是旧版参考。

| 模块 | 技术栈 | 状态 |
|------|--------|------|
| `app/` (前端) | Tauri v2 + React 18 + TypeScript + Vite | **主力** |
| `app/backend/` (主后端) | Rust + actix-web + SQLite | **主力** |
| `app/mineru-service/` (文档转换) | Rust + actix-web | 独立服务 |
| `app/src-tauri/` (Agent 模块) | Rust + reqwest | **Tauri Command** |
| `agent/` | Markdown + TypeScript | Agent 提示词模板 |
| `任务发布系统/` | Python + PySide6 + SQLite | 旧版参考 |
| `笔记处理系统/` | Python 脚本 | 旧版参考 |

## 当前项目架构

```
app/
├── src/                             ← React 前端
│   ├── lib/
│   │   ├── store.tsx                ← useReducer 状态管理（dispatch 自动同步后端）
│   │   ├── types.ts                 ← 全部数据模型
│   │   ├── api.ts                   ← REST API 客户端（38+ 函数）
│   │   ├── algorithms.ts            ← 加权随机算法（前端副实现）
│   │   ├── knowledge.ts             ← 知识库（后端优先，mock 降级）
│   │   ├── mineruClient.ts          ← MinerU 服务 REST 客户端
│   │   └── fileParser.ts            ← 浏览器端文件解析（pdfjs/mammoth/jszip）
│   ├── pages/                       ← 路由页面（Gacha / Tasks / Knowledge / etc.）
│   ├── components/                  ← 通用组件
│   └── styles/global.css            ← 主题变量（data-theme 切换 dark/light）
├── backend/                         ← Rust REST 后端（端口 8900）
│   └── src/
│       ├── main.rs                  ← 入口 + 路由注册 + CORS
│       ├── db.rs                    ← SQLite 初始化 + 建表
│       ├── models/                  ← 数据模型（task/gacha/schedule/state/knowledge）
│       ├── services/                ← 业务逻辑
│       │   ├── task_service.rs      ← 加权随机算法 + 链式解锁 + 循环检测
│       │   ├── gacha_service.rs     ← 连抽规划
│       │   └── knowledge_service.rs ← .md 文件扫描 + frontmatter 解析 + 链接分析 + 图谱
│       └── routes/                  ← REST handler（43+ 端点）
├── mineru-service/                  ← MinerU API 代理（端口 8899，独立服务）
└── src-tauri/                       ← Tauri Rust（greet + Agent Commands）
    └── src/agent/
        ├── commands.rs              ← run_agent / get_api_key_status / save_api_key
        ├── api_client.rs            ← Claude / OpenAI API 调用
        ├── key_manager.rs           ← API Key 文件存储
        └── prompts.rs               ← 5 个编译内嵌的 Agent System Prompt

agent/                               ← Agent 提示词 Markdown 源文件
└── prompts/                         ← content_reviewer / knowledge_extractor / etc.
```

## 后端架构模式

```
Database (db.rs: init_db + 12张表)
    ↓
Service (接收 &Connection，纯业务逻辑)
    ↓
Route (actix-web handler，序列化/反序列化)
```

- **状态共享**：`web::Data<AppState>` 包含 `Mutex<Connection>` + `notes_dir: PathBuf`
- **所有路由返回** `ApiResponse<T>` 统一 JSON 信封：`{success, data, error}`
- **camelCase JSON**：所有 `#[serde(rename_all = "camelCase")]` 对齐前端
- **笔记文件**：`.md` 文件存储在 `data/notes/`，含 YAML frontmatter（title/subject/tags/images）

## 前端架构模式

- **状态管理**：`useReducer` + `localStorage`（降级） + 异步同步后端（`store.tsx`）
- **dispatch 自动同步**：每次 dispatch 同时向后端发 REST 请求（fire-and-forget）
- **知识库**：`useKnowledgeBase()` 自动检测后端，在线时从后端加载，离线时 mock 数据
- **主题**：CSS 自定义属性 + `data-theme` 属性切换（dark/light），主色通过设置可调

## 关键算法（三端一致）

- **加权随机**：权重 = 基础 × priority/5 × deadlineUrgency × energyMatch × resistance × successRate × refusalPenalty × profileStrategy × cooldown
- **连抽规划**：<15min不抽 → 碎片(7min/块) → 番茄(25min) → 深度(50min) + 剩余
- **链式解锁**：完成任务后递归解锁所有满足前置条件的依赖任务（DFS）

## 常用命令

```bash
# 前端
cd app && npm install     # 安装依赖
cd app && npm run dev     # Vite 开发服务器
cd app && npx tsc --noEmit        # TypeScript 类型检查
cd app && npx vite build          # 生产构建
cd app && npm run tauri dev       # Tauri 桌面开发
cd app && npm run tauri build     # Tauri 构建

# 主后端（端口 8900）
cd app/backend && RUST_LOG=info cargo run

# MinerU 代理服务（端口 8899）
cd app/mineru-service && RUST_LOG=info cargo run

# Agent 独立环境变量配置
MINERU_API_KEY=xxx MINERU_API_URL=https://mineru.net \
  cd app/mineru-service && cargo run
```

## 数据库

- SQLite 文件：`app/backend/data/learning_tools.db`（可通过 `DB_PATH` 环境变量指定）
- 12 张核心表：tasks, tags, task_tags, daily_user_state, gacha_records, task_rejection_log, task_completion_feedback, user_schedule, daily_schedules, activities, settings, knowledge_points
- 笔记目录：`app/backend/data/notes/`（可通过 `NOTES_DIR` 环境变量指定）

## 文档

- `docs/api-documentation.md` — 完整的 REST API 规范（43+ 端点）
- `docs/backend-research.md` — Python 旧版分析 + 实施建议
