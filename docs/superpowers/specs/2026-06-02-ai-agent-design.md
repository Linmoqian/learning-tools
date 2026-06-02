# AI 学习助手 Agent 设计文档

## 概述

在 Tauri v2 桌面端应用 `app/` 中集成 AI Agent 功能，通过调用 Claude API 和 OpenAI API，为用户提供笔记整理、知识点提取、结构审查、内容审查四项智能处理能力。

## 架构

```
Frontend (React)               Tauri Rust Backend                  AI API
                    IPC                              HTTP
AgentPanel 组件 ──────→  agent_commands.rs ───────→ Anthropic / OpenAI
KnowledgePage 集成  ←─────  api_client.rs       ←──────
  (AgentSelector       prompt_loader.rs
   NoteSelector         key_manager.rs
   ResultDisplay)             │
                               ↕
                        agent/prompts/ (4 个 .md 文件)
```

## 文件结构

### 1. `agent/` 目录（项目根目录）

```
agent/
├── prompts/
│   ├── note_organizer.md         # 笔记整理 Agent
│   ├── knowledge_extractor.md    # 知识点整理 Agent
│   ├── structure_reviewer.md     # 结构审查 Agent
│   └── content_reviewer.md       # 内容审查 Agent
├── config.ts                     # API 配置（provider、模型选择）
├── types.ts                      # Agent 相关类型定义
└── api-client.ts                 # 统一 API 客户端
```

### 2. Tauri Rust 后端

```
app/src-tauri/src/
├── agent/
│   ├── mod.rs                    # 模块入口
│   ├── commands.rs               # Tauri Command 定义
│   ├── api_client.rs             # HTTP 调用 AI API
│   ├── prompt_loader.rs          # 读取 prompt 文件
│   └── key_manager.rs            # API Key 存储管理
```

### 3. React 前端

```
app/src/components/
└── AgentPanel.tsx                # Agent 操作面板

app/src/pages/KnowledgePage.tsx   # 新增 agent tab
```

## Tauri Rust 后端设计

### Tauri Command

提供 3 个 Tauri Command：

| Command | 参数 | 返回 |
|---------|------|------|
| `run_agent` | `{ agent_type, note_content, provider?, model? }` | `AgentResult` |
| `get_prompt` | `{ agent_type }` | prompt 纯文本 |
| `get_api_key_status` | - | `{ claude: bool, openai: bool }` |

### ApiClient

- 使用 `reqwest` 库发送 HTTP 请求
- 支持 Anthropic Messages API 和 OpenAI Chat Completions API
- 通过 `provider` 参数路由到对应端点
- 超时设置 60 秒

### KeyManager

- 使用 `tauri-plugin-store` 加密存储 API Key
- Key 在 Tauri 侧管理，前端不接触原始 Key
- 支持 `save_key(provider, key)` 和 `get_key(provider) → Option<String>`

## 前端设计

### AgentPanel 组件

```
AgentPanel
├── ProviderSelector    — Claude / OpenAI 切换 + 模型下拉
├── AgentSelector       — 4 个 Agent 按钮（单次只能选一个）
├── NoteSelector        — 笔记选择器（从知识库列���选择）
├── ResultDisplay       — Markdown 渲染结果
│   ├── 加载状态：旋转动画 + "正在分析..."
│   ├── 成功状态：Markdown 渲染内容
│   ├── 错误状态：错误信息 + 重试按钮
│   └── 空状态："选择笔记和 Agent 后开始"
└── ActionButtons       — 运行 / 保存结果 / 复制结果
```

### KnowledgePage 集成

- 在现有 3 个 Tab（browse / graph / analysis）基础上新增第 4 个 Tab —— "Agent"
- Agent 分析结果可以保存到笔记中

## API 请求格式

### Claude API

```
POST https://api.anthropic.com/v1/messages
Headers: x-api-key, anthropic-version: 2023-06-01
Body: {
  model: "claude-sonnet-4-20250514",
  max_tokens: 4096,
  system: prompt,
  messages: [{ role: "user", content: note_content }]
}
```

### OpenAI API

```
POST https://api.openai.com/v1/chat/completions
Headers: Authorization: Bearer
Body: {
  model: "gpt-4o",
  messages: [
    { role: "system", content: prompt },
    { role: "user", content: note_content }
  ]
}
```

## Agent Prompt 设计

每个 prompt 文件包含 system prompt 和输出格式要求，运行时与笔记内容拼接后发送给 AI API。

### 笔记整理 Agent
- 对笔记内容进行结构化整理
- 纠正错别��、优化表达
- 补充缺失的关键概念

### 知识点整理 Agent
- 从笔记中提取核心知识点
- 建立知识点之间的联系
- 输出可导入知识库的结构化数据

### 结构审查 Agent
- 审查笔记的章节结构和逻辑层次
- 提出结构优化建议
- 检查是否有章节缺失或冗余

### 内容审查 Agent
- 审查内容准确性和完整性
- 检查是否存在概念错误
- 评估内容深度是否足够

## 交互流程

```
用户选择笔记 → 选择 Agent → 选择 Provider/模型 → 点击运行
                                                    ↓
                                          [Loading 动画]
                                          Tauri Command
                                          → Rust 读取 prompt
                                          → Rust 调用 AI API
                                          → Rust 返回结果
                                                    ↓
                                              显示 Markdown 结果
                                              [保存 / 复制选项]
```

## 错误处理

| 场景 | 表现 |
|------|------|
| API Key 未配置 | 提示用户配置 Key，显示配置入口 |
| API 调用失败 | 显示具体错误信息 + 重试按钮 |
| Provider 不可用 | 提示切换 Provider |
| 笔记内容为空 | 前置校验，禁用运行按钮 |
| API 超时 | 提示 60 秒超时，建议重试 |

## 测试方案

1. Rust 单元测试：api_client 请求构建、prompt_loader 文件读取
2. React 组件测试：AgentPanel 各状态渲染
3. 手动测试：在 app 中实际调用各 Agent 处理笔记

## 排除范围

- 不实现流式响应（SSE）
- 不做 Agent 运行历史持久化（仅当前 session 可见）
- 不实现批量处理多个笔记
- 不实现自定义 prompt 编辑
