# 学习工具

基于 Tauri v2 + React 18 + Rust actix-web 的桌面学习工具集。

## 功能概览

| 功能 | 说明 |
|------|------|
| **任务管理** | 创建任务、加权随机抽卡、链式解锁、废牌堆、周期重置 |
| **抽卡系统** | 按权重随机抽取任务，连抽规划（碎片/番茄/深度），拒绝惩罚 |
| **知识库** | Markdown 笔记管理，YAML frontmatter 解析，链接分析，知识图谱 |
| **AI Agent** | 基于知识库的问答 Agent，流式输出，思考过程展示 |
| **日程管理** | 每日时段规划，活动记录，早睡打卡 |
| **状态追踪** | 精力/心情评估，任务反馈，灰度趋势 |
| **文档转换** | MinerU 服务集成，任意文件转 Markdown |
| **新手指引** | 内置操作引导，可在设置重新打开 |

## 项目架构

```
app/
├── src/                      ← React 前端
│   ├── pages/                ← 路由页面（8 个页面）
│   ├── components/           ← 通用组件（15 个组件）
│   ├── lib/                  ← 核心逻辑
│   │   ├── store.tsx         ← useReducer 状态管理 + 后端自动同步
│   │   ├── api.ts            ← REST API 客户端
│   │   ├── algorithms.ts     ← 加权随机算法 / 链式解锁 / 连抽规划
│   │   └── knowledge.ts      ← 知识库操作
│   └── styles/global.css     ← 主题变量（dark/light 切换）
├── backend/                  ← Rust actix-web 后端（端口 8900）
│   └── src/
│       ├── routes/           ← REST 路由（43+ 端点）
│       ├── services/         ← 业务逻辑层
│       ├── models/           ← 数据模型
│       ├── db.rs             ← SQLite 初始化（12 张表）
│       └── main.rs           ← 入口 + CORS
├── mineru-service/           ← 文档转换独立服务（端口 8899）
└── src-tauri/                ← Tauri Rust 层
    └── src/agent/            ← AI Agent 模块（commands / api_client / key_manager / prompts）
```

## 开发

```bash
# 安装依赖
cd app && npm install

# 前端开发（Vite）
cd app && npm run dev

# Rust 后端开发（端口 8900）
cd app/backend && RUST_LOG=info cargo run

# Tauri 桌面开发
cd app && npm run tauri dev

# 类型检查
cd app && npx tsc --noEmit

# 生产构建
cd app && npm run tauri build
```

构建产物位于 `app/src-tauri/target/release/bundle/`，支持 MSI 和 NSIS 安装包。

## 技术栈

- **前端**: Tauri v2 + React 18 + TypeScript + Vite
- **后端**: Rust + actix-web + SQLite
- **AI Agent**: Anthropic Claude API / OpenAI API
- **文档解析**: MinerU API
- **主题**: CSS 自定义属性 + `data-theme` 切换
- **状态管理**: useReducer + localStorage 降级 + REST 同步

## 参考项目

- [Tauri](https://tauri.app/) — 跨平台桌面应用框架
- [MinerU](https://github.com/opendatalab/mineru) — 多格式文档转 Markdown
