# AI 学习助手 Agent 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 在 Tauri v2 桌面端应用中集成 AI Agent 功能，支持通过 Claude/OpenAI API 进行笔记整理、知识点提取、结构审查、内容审查。

**架构：** React 前端通过 Tauri Command 调用 Rust 后端，Rust 使用 reqwest 调用 AI API。API Key 存储在用户数据目录的 JSON 文件中。Agent Prompt 模板编译到 Rust 二进制中。

**Tech Stack:** Tauri v2, Rust (reqwest, serde), React 18, TypeScript, Claude API / OpenAI API

---

## 文件结构

### 新文件

| 文件 | 职责 |
|------|------|
| `agent/prompts/note_organizer.md` | 笔记整理 Agent prompt 模板 |
| `agent/prompts/knowledge_extractor.md` | 知识点整理 Agent prompt 模板 |
| `agent/prompts/structure_reviewer.md` | 结构审查 Agent prompt 模板 |
| `agent/prompts/content_reviewer.md` | 内容审查 Agent prompt 模板 |
| `agent/types.ts` | Agent 相关 TypeScript 类型定义 |
| `app/src-tauri/src/agent/mod.rs` | Rust agent 模块入口 |
| `app/src-tauri/src/agent/prompts.rs` | 嵌入 prompt 文本的 Rust 常量 |
| `app/src-tauri/src/agent/api_client.rs` | AI API HTTP 客户端 |
| `app/src-tauri/src/agent/key_manager.rs` | API Key 文件存储管理 |
| `app/src-tauri/src/agent/commands.rs` | Tauri Command 定义 |
| `app/src/components/AgentPanel.tsx` | Agent 操作面板组件 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `app/src-tauri/Cargo.toml` | 添加 reqwest 依赖 |
| `app/src-tauri/src/lib.rs` | 注册 agent 模块和 Command |
| `app/src/pages/KnowledgePage.tsx` | 新增 Agent 标签页 |

---

### Task 1: 创建 Agent Prompt 模板文件

**Files:**
- Create: `agent/prompts/note_organizer.md`
- Create: `agent/prompts/knowledge_extractor.md`
- Create: `agent/prompts/structure_reviewer.md`
- Create: `agent/prompts/content_reviewer.md`

- [ ] **Step 1: 创建笔记整理 prompt**

```markdown
Write `agent/prompts/note_organizer.md`:

# 角色
你是一名专业的学习笔记整理助手。你擅长将零散的笔记内容整理成结构清晰、逻辑连贯的学习笔记。

# 任务
整理用户提供的笔记内容，执行以下操作：
1. 修正错别字和语法错误
2. 统一术语和表达方式
3. 补充缺失的关键概念和背景信息
4. 优化段落结构和逻辑顺序
5. 添加适当的小标题和层级结构
6. 保留原始笔记中的所有重要信息

# 输出格式
请按以下 JSON 格式返回结果：
{
  "title": "整理后的笔记标题",
  "summary": "50字以内的摘要",
  "content": "整理后的完整笔记内容（Markdown格式）",
  "changes": [
    "修正了 X 处错别字",
    "补充了 Y 概念的解释"
  ]
}

# 注意事项
- 不要编造不存在的概念
- 如果笔记内容过于简略无法整理，请说明需要补充的信息
- 保留原笔记的核心观点和论证
```

- [ ] **Step 2: 创建知识点提取 prompt**

```markdown
Write `agent/prompts/knowledge_extractor.md`:

# 角色
你是一名知识工程专家，擅长从学习笔记中提取结构化知识点，构建知识网络。

# 任务
从用户提供的笔记内容中提取核心知识点，执行以下操作：
1. 识别笔记中涉及的所有核心知识点
2. 为每个知识点提供清晰的定义和描述
3. 标注知识点之间的关联关系（前置/后置/并列）
4. 将知识点归类到合适的学科分类

# 输出格式
请按以下 JSON 格式返回结果：
{
  "knowledgePoints": [
    {
      "name": "知识点名称",
      "description": "知识点简要定义和说明（50-100字）",
      "subject": "所属学科",
      "prerequisites": ["前置知识点名称"],
      "relatedPoints": ["相关知识点的名称"]
    }
  ],
  "summary": "总体知识覆盖情况说明",
  "suggestedTags": ["标签1", "标签2"]
}

# 注意事项
- 知识点粒度要适中，不宜过细（每个步骤）也不宜过粗（整章内容）
- 关联关系标注要准确，不要强行关联无关概念
```

- [ ] **Step 3: 创建结构审查 prompt**

```markdown
Write `agent/prompts/structure_reviewer.md`:

# 角色
你是一名教学设计专家，擅长评估学习笔记的结构质量和逻辑框架。

# 任务
审查用户提供的笔记结构，执行以下操作：
1. 评估章节划分的合理性
2. 检查逻辑递进关系是否清晰
3. 识别缺少的关键章节或内容板块
4. 发现内容冗余或重复的部分
5. 评估各章节篇幅是否均衡

# 输出格式
请按以下 JSON 格式返回结果：
{
  "overallScore": 85,
  "structureMap": [
    {
      "section": "章节标题",
      "level": 1,
      "assessment": "合理/偏短/偏长/冗余",
      "suggestion": "建议..."
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
  "summary": "总体结构评价（100-200字）"
}
```

- [ ] **Step 4: 创建内容审查 prompt**

```markdown
Write `agent/prompts/content_reviewer.md`:

# 角色
你是一名学科专家，擅长评估学习笔记的内容质量、准确性和完整性。

# 任务
审查用户提供的笔记内容质量，执行以下操作：
1. 检查概念定义是否准确
2. 验证公式、定理、原理的表述是否正确
3. 评估内容深度是否匹配学习阶段
4. 检查例证和应用的恰当性
5. 发现内容错误或表述不严谨之处

# 输出格式
请按以下 JSON 格式返回结果：
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
  "completeness": {
    "score": 80,
    "missingPoints": ["缺失的关键概念或内容"]
  },
  "depth": {
    "score": 85,
    "assessment": "深度评价",
    "suggestions": ["深度提升建议"]
  },
  "summary": "总体内容评价（100-200字）"
}
```

- [ ] **Step 5: 提交**

```bash
git add agent/prompts/
git commit -m "feat: 添加 4 个 Agent prompt 模板文件"
```

---

### Task 2: 创建 Agent TypeScript 类型定义

**Files:**
- Create: `agent/types.ts`

- [ ] **Step 1: 创建 types.ts**

Write `agent/types.ts`:

```typescript
// ===== Agent Types =====

export const AGENT_TYPES = [
  'note_organizer',
  'knowledge_extractor',
  'structure_reviewer',
  'content_reviewer',
] as const;
export type AgentType = (typeof AGENT_TYPES)[number];

export const AGENT_LABELS: Record<AgentType, string> = {
  note_organizer: '笔记整理',
  knowledge_extractor: '知识点整理',
  structure_reviewer: '结构审查',
  content_reviewer: '内容审查',
};

export const AGENT_DESCRIPTIONS: Record<AgentType, string> = {
  note_organizer: '对笔记内容进行结构化整理、修正错别字、补充关键概念',
  knowledge_extractor: '从笔记中提取核心知识点，建立知识点间的关联关系',
  structure_reviewer: '审查笔记的章节结构和逻辑层次，提出结构优化建议',
  content_reviewer: '审查内容的准确性和完整性，检查概念错误和表述问题',
};

export type AIProvider = 'claude' | 'openai';

export const PROVIDER_LABELS: Record<AIProvider, string> = {
  claude: 'Claude',
  openai: 'OpenAI',
};

export const PROVIDER_MODELS: Record<AIProvider, string[]> = {
  claude: ['claude-sonnet-4-20250514', 'claude-3-5-haiku-20241022'],
  openai: ['gpt-4o', 'gpt-4o-mini'],
};

export const DEFAULT_MODELS: Record<AIProvider, string> = {
  claude: 'claude-sonnet-4-20250514',
  openai: 'gpt-4o',
};

export interface RunAgentRequest {
  agentType: AgentType;
  noteContent: string;
  provider?: AIProvider;
  model?: string;
}

export interface AgentResult {
  content: string;
  model: string;
  provider: string;
}

export interface ApiKeyStatus {
  claude: boolean;
  openai: boolean;
}

export interface AgentError {
  message: string;
  code: 'missing_key' | 'api_error' | 'network_error' | 'parse_error' | 'timeout';
}
```

- [ ] **Step 2: 提交**

```bash
git add agent/types.ts
git commit -m "feat: 添加 Agent TypeScript 类型定义"
```

---

### Task 3: 添加 Rust 依赖

**Files:**
- Modify: `app/src-tauri/Cargo.toml`

- [ ] **Step 1: 修改 Cargo.toml 添加 reqwest 和 tokio**

Edit `app/src-tauri/Cargo.toml`, add after `serde_json` line:

```toml
reqwest = { version = "0.12", default-features = false, features = ["json", "rustls-tls"] }
tokio = { version = "1", features = ["full"] }
```

- [ ] **Step 2: 提交**

```bash
git add app/src-tauri/Cargo.toml
git commit -m "chore: 添加 reqwest 和 tokio 依赖"
```

---

### Task 4: 创建 Rust Agent 模块

**Files:**
- Create: `app/src-tauri/src/agent/mod.rs`
- Create: `app/src-tauri/src/agent/prompts.rs`
- Create: `app/src-tauri/src/agent/api_client.rs`
- Create: `app/src-tauri/src/agent/key_manager.rs`
- Create: `app/src-tauri/src/agent/commands.rs`

- [ ] **Step 1: 创建 prompts.rs（嵌入 4 个 prompt 文本）**

Create `app/src-tauri/src/agent/prompts.rs`:

```rust
pub fn get_prompt(agent_type: &str) -> Option<&'static str> {
    match agent_type {
        "note_organizer" => Some(NOTE_ORGANIZER),
        "knowledge_extractor" => Some(KNOWLEDGE_EXTRACTOR),
        "structure_reviewer" => Some(STRUCTURE_REVIEWER),
        "content_reviewer" => Some(CONTENT_REVIEWER),
        _ => None,
    }
}

// NOTE: These are compiled-in copies of the .md files in agent/prompts/.
// Keep them in sync when editing prompts.

const NOTE_ORGANIZER: &str = r#"# 角色
你是一名专业的学习笔记整理助手。你擅长将零散的笔记内容整理成结构清晰、逻辑连贯的学习笔记。

# 任务
整理用户提供的笔记内容，执行以下操作：
1. 修正错别字和语法错误
2. 统一术语和表达方式
3. 补充缺失的关键概念和背景信息
4. 优化段落结构和逻辑顺序
5. 添加适当的小标题和层级结构
6. 保留原始笔记中的所有重要信息

# 输出格式
请按以下 JSON 格式返回结果：
{
  "title": "整理后的笔记标题",
  "summary": "50字以内的摘要",
  "content": "整理后的完整笔记内容（Markdown格式）",
  "changes": [
    "修正了 X 处错别字",
    "补充了 Y 概念的解释"
  ]
}

# 注意事项
- 不要编造不存在的概念
- 如果笔记内容过于简略无法整理，请说明需要补充的信息
- 保留原笔记的核心观点和论证"#;

const KNOWLEDGE_EXTRACTOR: &str = r#"# 角色
你是一名知识工程专家，擅长从学习笔记中提取结构化知识点，构建知识网络。

# 任务
从用户提供的笔记内容中提取核心知识点，执行以下操作：
1. 识别笔记中涉及的所有核心知识点
2. 为每个知识点提供清晰的定义和描述
3. 标注知识点之间的关联关系（前置/后置/并列）
4. 将知识点归类到合适的学科分类

# 输出格式
请按以下 JSON 格式返回结果：
{
  "knowledgePoints": [
    {
      "name": "知识点名称",
      "description": "知识点简要定义和说明（50-100字）",
      "subject": "所属学科",
      "prerequisites": ["前置知识点名称"],
      "relatedPoints": ["相关知识点的名称"]
    }
  ],
  "summary": "总体知识覆盖情况说明",
  "suggestedTags": ["标签1", "标签2"]
}

# 注意事项
- 知识点粒度要适中，不宜过细（每个步骤）也不宜过粗（整章内容）
- 关联关系标注要准确，不要强行关联无关概念"#;

const STRUCTURE_REVIEWER: &str = r#"# 角色
你是一名教学设计专家，擅长评估学习笔记的结构质量和逻辑框架。

# 任务
审查用户提供的笔记结构，执行以下操作：
1. 评估章节划分的合理性
2. 检查逻辑递进关系是否清晰
3. 识别缺少的关键章节或内容板块
4. 发现内容冗余或重复的部分
5. 评估各章节篇幅是否均衡

# 输出格式
请按以下 JSON 格式返回结果：
{
  "overallScore": 85,
  "structureMap": [
    {
      "section": "章节标题",
      "level": 1,
      "assessment": "合理/偏短/偏长/冗余",
      "suggestion": "建议..."
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
  "summary": "总体结构评价（100-200字）"
}"#;

const CONTENT_REVIEWER: &str = r#"# 角色
你是一名学科专家，擅长评估学习笔记的内容质量、准确性和完整性。

# 任务
审查用户提供的笔记内容质量，执行以下操作：
1. 检查概念定义是否准确
2. 验证公式、定理、原理的表述是否正确
3. 评估内容深度是否匹配学习阶段
4. 检查例证和应用的恰当性
5. 发现内容错误或表述不严谨之处

# 输出格式
请按以下 JSON 格式返回结果：
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
  "completeness": {
    "score": 80,
    "missingPoints": ["缺失的关键概念或内容"]
  },
  "depth": {
    "score": 85,
    "assessment": "深度评价",
    "suggestions": ["深度提升建议"]
  },
  "summary": "总体内容评价（100-200字）"
}"#;
```

- [ ] **Step 2: 创建 api_client.rs**

Create `app/src-tauri/src/agent/api_client.rs`:

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct AgentResult {
    pub content: String,
    pub model: String,
    pub provider: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeMessage {
    role: String,
    content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ClaudeRequest {
    model: String,
    max_tokens: u32,
    system: String,
    messages: Vec<ClaudeMessage>,
}

#[derive(Debug, Deserialize)]
struct ClaudeResponse {
    content: Vec<ClaudeContent>,
    model: String,
}

#[derive(Debug, Deserialize)]
struct ClaudeContent {
    text: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct OpenAIMessage {
    role: String,
    content: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct OpenAIRequest {
    model: String,
    messages: Vec<OpenAIMessage>,
    max_tokens: u32,
}

#[derive(Debug, Deserialize)]
struct OpenAIResponse {
    choices: Vec<OpenAIChoice>,
    model: String,
}

#[derive(Debug, Deserialize)]
struct OpenAIChoice {
    message: OpenAIMessage,
}

pub async fn call_claude(
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_content: &str,
) -> Result<AgentResult, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(90))
        .build()
        .map_err(|e| format!("创建 HTTP 客户端失败: {}", e))?;

    let request = ClaudeRequest {
        model: model.to_string(),
        max_tokens: 4096,
        system: system_prompt.to_string(),
        messages: vec![ClaudeMessage {
            role: "user".to_string(),
            content: user_content.to_string(),
        }],
    };

    let response = client
        .post("https://api.anthropic.com/v1/messages")
        .header("x-api-key", api_key)
        .header("anthropic-version", "2023-06-01")
        .header("content-type", "application/json")
        .json(&request)
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                "API 请求超时（90秒），请重试".to_string()
            } else if e.is_connect() {
                format!("网络连接失败: {}", e)
            } else {
                format!("API 请求失败: {}", e)
            }
        })?;

    let status = response.status();
    let body = response.text().await.map_err(|e| format!("读取响应失败: {}", e))?;

    if !status.is_success() {
        return Err(format!("Claude API 返回错误 ({}): {}", status.as_u16(), body));
    }

    let claude_resp: ClaudeResponse = serde_json::from_str(&body)
        .map_err(|e| format!("解析响应失败: {}", e))?;

    let content = claude_resp.content.into_iter()
        .map(|c| c.text)
        .collect::<Vec<_>>()
        .join("\n");

    Ok(AgentResult {
        content,
        model: claude_resp.model,
        provider: "claude".to_string(),
    })
}

pub async fn call_openai(
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_content: &str,
) -> Result<AgentResult, String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(90))
        .build()
        .map_err(|e| format!("创建 HTTP 客户端失败: {}", e))?;

    let request = OpenAIRequest {
        model: model.to_string(),
        max_tokens: 4096,
        messages: vec![
            OpenAIMessage {
                role: "system".to_string(),
                content: system_prompt.to_string(),
            },
            OpenAIMessage {
                role: "user".to_string(),
                content: user_content.to_string(),
            },
        ],
    };

    let response = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {}", api_key))
        .header("content-type", "application/json")
        .json(&request)
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                "API 请求超时（90秒），请重试".to_string()
            } else if e.is_connect() {
                format!("网络连接失败: {}", e)
            } else {
                format!("API 请求失败: {}", e)
            }
        })?;

    let status = response.status();
    let body = response.text().await.map_err(|e| format!("读取响应失败: {}", e))?;

    if !status.is_success() {
        return Err(format!("OpenAI API 返回错误 ({}): {}", status.as_u16(), body));
    }

    let openai_resp: OpenAIResponse = serde_json::from_str(&body)
        .map_err(|e| format!("解析响应失败: {}", e))?;

    let content = openai_resp.choices.into_iter()
        .next()
        .map(|c| c.message.content)
        .unwrap_or_default();

    Ok(AgentResult {
        content,
        model: openai_resp.model,
        provider: "openai".to_string(),
    })
}
```

- [ ] **Step 3: 创建 key_manager.rs**

Create `app/src-tauri/src/agent/key_manager.rs`:

```rust
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize, Default)]
struct ApiKeys {
    claude: Option<String>,
    openai: Option<String>,
}

fn get_keys_path(app_data_dir: &PathBuf) -> PathBuf {
    app_data_dir.join("api_keys.json")
}

pub fn save_key(app_data_dir: &PathBuf, provider: &str, key: &str) -> Result<(), String> {
    let path = get_keys_path(app_data_dir);
    let mut keys: ApiKeys = load_keys_internal(app_data_dir);

    match provider {
        "claude" => keys.claude = Some(key.to_string()),
        "openai" => keys.openai = Some(key.to_string()),
        _ => return Err(format!("未知 provider: {}", provider)),
    }

    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| format!("创建目录失败: {}", e))?;
    }

    let json = serde_json::to_string_pretty(&keys)
        .map_err(|e| format!("序列化失败: {}", e))?;
    std::fs::write(&path, json).map_err(|e| format!("写入文件失败: {}", e))?;

    Ok(())
}

pub fn get_key(app_data_dir: &PathBuf, provider: &str) -> Option<String> {
    let keys = load_keys_internal(app_data_dir);
    match provider {
        "claude" => keys.claude,
        "openai" => keys.openai,
        _ => None,
    }
}

fn load_keys_internal(app_data_dir: &PathBuf) -> ApiKeys {
    let path = get_keys_path(app_data_dir);
    if !path.exists() {
        return ApiKeys::default();
    }
    let content = std::fs::read_to_string(&path).ok()?;
    serde_json::from_str(&content).unwrap_or_default()
}

pub fn get_key_status(app_data_dir: &PathBuf) -> (bool, bool) {
    let keys = load_keys_internal(app_data_dir);
    (keys.claude.is_some(), keys.openai.is_some())
}
```

- [ ] **Step 4: 创建 commands.rs**

Create `app/src-tauri/src/agent/commands.rs`:

```rust
use super::api_client::{self, AgentResult};
use super::key_manager;
use super::prompts;
use tauri::Manager;

#[derive(serde::Deserialize)]
pub struct RunAgentRequest {
    pub agent_type: String,
    pub note_content: String,
    pub provider: Option<String>,
    pub model: Option<String>,
}

#[derive(serde::Serialize)]
pub struct KeyStatusResult {
    pub claude: bool,
    pub openai: bool,
}

#[tauri::command]
pub async fn run_agent(
    app: tauri::AppHandle,
    request: RunAgentRequest,
) -> Result<AgentResult, String> {
    let agent_type = &request.agent_type;
    let note_content = &request.note_content;
    let provider = request.provider.as_deref().unwrap_or("claude");
    let model = request.model.as_deref().unwrap_or("");

    if note_content.trim().is_empty() {
        return Err("笔记内容不能为空".to_string());
    }

    // Get prompt
    let prompt = prompts::get_prompt(agent_type)
        .ok_or_else(|| format!("未知的 Agent 类型: {}", agent_type))?;

    // Resolve model
    let resolved_model = if model.is_empty() {
        match provider {
            "claude" => "claude-sonnet-4-20250514",
            "openai" => "gpt-4o",
            _ => return Err(format!("未知的 provider: {}", provider)),
        }
    } else {
        model
    };

    // Get API key
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("获取应用数据目录失败: {}", e))?;

    let api_key = key_manager::get_key(&app_data_dir, provider)
        .ok_or_else(|| format!("{} API Key 未配置，请在设置中输入", provider))?;

    // Call API
    match provider {
        "claude" => api_client::call_claude(&api_key, resolved_model, prompt, note_content).await,
        "openai" => api_client::call_openai(&api_key, resolved_model, prompt, note_content).await,
        _ => Err(format!("未知的 provider: {}", provider)),
    }
}

#[tauri::command]
pub async fn get_api_key_status(app: tauri::AppHandle) -> Result<KeyStatusResult, String> {
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("获取应用数据目录失败: {}", e))?;
    let (claude, openai) = key_manager::get_key_status(&app_data_dir);
    Ok(KeyStatusResult { claude, openai })
}

#[tauri::command]
pub async fn save_api_key(
    app: tauri::AppHandle,
    provider: String,
    key: String,
) -> Result<(), String> {
    if key.trim().is_empty() {
        return Err("API Key 不能为空".to_string());
    }
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("获取应用数据目录失败: {}", e))?;
    key_manager::save_key(&app_data_dir, &provider, &key)
}

#[tauri::command]
pub async fn get_prompt_content(agent_type: String) -> Result<String, String> {
    prompts::get_prompt(&agent_type)
        .map(|s| s.to_string())
        .ok_or_else(|| format!("未知的 Agent 类型: {}", agent_type))
}
```

- [ ] **Step 5: 创建 mod.rs**

Create `app/src-tauri/src/agent/mod.rs`:

```rust
pub mod api_client;
pub mod commands;
pub mod key_manager;
pub mod prompts;
```

- [ ] **Step 6: 提交**

```bash
git add app/src-tauri/src/agent/
git commit -m "feat: 添加 Rust Agent 模块（prompts/api_client/key_manager/commands）"
```

---

### Task 5: 注册 Tauri Command

**Files:**
- Modify: `app/src-tauri/src/lib.rs`

- [ ] **Step 1: 修改 lib.rs 注册 agent 模块和 commands**

Edit `app/src-tauri/src/lib.rs`, replace entire file:

```rust
mod agent;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            agent::commands::run_agent,
            agent::commands::get_api_key_status,
            agent::commands::save_api_key,
            agent::commands::get_prompt_content,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

- [ ] **Step 2: 验证 Rust 编译**

Run: `cd app && cargo check 2>&1 | head -50`
Expected: 编译成功，无错误

- [ ] **Step 3: 提交**

```bash
git add app/src-tauri/src/lib.rs
git commit -m "feat: 注册 Agent Tauri Command"
```

---

### Task 6: 创建 AgentPanel React 组件

**Files:**
- Create: `app/src/components/AgentPanel.tsx`

- [ ] **Step 1: 创建 AgentPanel 组件**

Write `app/src/components/AgentPanel.tsx`:

```tsx
import { useState, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles, FileText, Settings, Play, CheckCircle,
  AlertCircle, Loader2, Copy, Save, FileDown,
} from 'lucide-react';
import { invoke } from '@tauri-apps/api/core';
import {
  type AgentType, type AIProvider, type AgentResult, type ApiKeyStatus,
  AGENT_TYPES, AGENT_LABELS, AGENT_DESCRIPTIONS,
  PROVIDER_LABELS, PROVIDER_MODELS, DEFAULT_MODELS,
} from '../../agent/types';

interface Note {
  id: string;
  title: string;
  subject: string;
  content: string;
}

type Status = 'idle' | 'loading' | 'success' | 'error';

export default function AgentPanel({ notes }: { notes: Note[] }) {
  const [agentType, setAgentType] = useState<AgentType>('note_organizer');
  const [selectedNoteId, setSelectedNoteId] = useState<string>('');
  const [provider, setProvider] = useState<AIProvider>('claude');
  const [model, setModel] = useState(DEFAULT_MODELS.claude);
  const [status, setStatus] = useState<Status>('idle');
  const [result, setResult] = useState<AgentResult | null>(null);
  const [error, setError] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [claudeKey, setClaudeKey] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [keyStatus, setKeyStatus] = useState<ApiKeyStatus>({ claude: false, openai: false });

  const selectedNote = notes.find(n => n.id === selectedNoteId);

  // Load API key status
  useEffect(() => {
    invoke<ApiKeyStatus>('get_api_key_status')
      .then(setKeyStatus)
      .catch(() => {});
  }, []);

  const handleRun = useCallback(async () => {
    if (!selectedNote) return;

    setStatus('loading');
    setResult(null);
    setError('');

    try {
      const res = await invoke<AgentResult>('run_agent', {
        request: {
          agentType,
          noteContent: selectedNote.content,
          provider,
          model,
        },
      });
      setResult(res);
      setStatus('success');
    } catch (e) {
      setError(typeof e === 'string' ? e : '运行 Agent 失败');
      setStatus('error');
    }
  }, [agentType, selectedNote, provider, model]);

  const handleSaveKey = useCallback(async (providerName: string, key: string) => {
    try {
      await invoke('save_api_key', { provider: providerName, key });
      setKeyStatus(prev => ({ ...prev, [providerName]: true }));
    } catch (e) {
      setError(typeof e === 'string' ? e : '保存失败');
    }
  }, []);

  const handleCopyResult = useCallback(() => {
    if (result?.content) {
      navigator.clipboard.writeText(result.content);
    }
  }, [result]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, height: '100%' }}>
      {/* API Settings bar */}
      <div className="glass" style={{ padding: '10px 16px', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: '#6b6480' }}>API: </span>
          {(['claude', 'openai'] as const).map(p => (
            <span key={p} style={{
              fontSize: 11, padding: '2px 8px', borderRadius: 4,
              background: keyStatus[p] ? 'rgba(39,174,96,0.1)' : 'rgba(231,76,60,0.1)',
              color: keyStatus[p] ? '#27ae60' : '#e74c3c',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: keyStatus[p] ? '#27ae60' : '#e74c3c' }} />
              {PROVIDER_LABELS[p]}
            </span>
          ))}
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          style={{ padding: '6px 12px', borderRadius: 6, border: 'none', background: 'rgba(255,255,255,0.06)', color: '#a8a0b8', fontSize: 12, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Settings size={14} />
          配置 API Key
        </button>
      </div>

      {/* Settings panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }}
            className="glass" style={{ padding: 16, borderRadius: 10, overflow: 'hidden' }}
          >
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 12, color: '#a8a0b8', marginBottom: 4, display: 'block' }}>Claude API Key</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="password"
                    value={claudeKey}
                    onChange={e => setClaudeKey(e.target.value)}
                    placeholder="sk-ant-..."
                    style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.04)', color: '#f0e8da', fontSize: 12, outline: 'none' }}
                  />
                  <button onClick={() => handleSaveKey('claude', claudeKey)} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'rgba(240,192,64,0.15)', color: '#f0c040', fontSize: 12, cursor: 'pointer' }}>保存</button>
                </div>
              </div>
              <div>
                <label style={{ fontSize: 12, color: '#a8a0b8', marginBottom: 4, display: 'block' }}>OpenAI API Key</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    type="password"
                    value={openaiKey}
                    onChange={e => setOpenaiKey(e.target.value)}
                    placeholder="sk-..."
                    style={{ flex: 1, padding: '8px 12px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.04)', color: '#f0e8da', fontSize: 12, outline: 'none' }}
                  />
                  <button onClick={() => handleSaveKey('openai', openaiKey)} style={{ padding: '8px 16px', borderRadius: 6, border: 'none', background: 'rgba(240,192,64,0.15)', color: '#f0c040', fontSize: 12, cursor: 'pointer' }}>保存</button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Control row: Agent + Provider + Model */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
        {/* Agent selector */}
        <div className="glass" style={{ padding: 12, borderRadius: 10, flex: 1, minWidth: 200 }}>
          <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择 Agent</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {AGENT_TYPES.map(at => (
              <button
                key={at}
                onClick={() => { setAgentType(at); setStatus('idle'); }}
                style={{
                  padding: '8px 12px', borderRadius: 8, border: 'none', textAlign: 'left',
                  background: agentType === at ? 'rgba(240,192,64,0.12)' : 'rgba(255,255,255,0.03)',
                  border: agentType === at ? '1px solid rgba(240,192,64,0.2)' : '1px solid transparent',
                  color: agentType === at ? '#f0c040' : '#a8a0b8',
                  fontSize: 12, cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 2 }}>{AGENT_LABELS[at]}</div>
                <div style={{ fontSize: 10, color: '#6b6480' }}>{AGENT_DESCRIPTIONS[at]}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Note + Provider selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 200 }}>
          {/* Note selector */}
          <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
            <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>选择笔记</div>
            <select
              value={selectedNoteId}
              onChange={e => { setSelectedNoteId(e.target.value); setStatus('idle'); }}
              style={{
                width: '100%', padding: '8px 12px', borderRadius: 6,
                border: '1px solid rgba(255,255,255,0.08)',
                background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                fontSize: 12, outline: 'none',
              }}
            >
              <option value="">-- 请选择笔记 --</option>
              {notes.map(n => (
                <option key={n.id} value={n.id}>
                  [{n.subject}] {n.title}
                </option>
              ))}
            </select>
          </div>

          {/* Provider + Model */}
          <div className="glass" style={{ padding: 12, borderRadius: 10 }}>
            <div style={{ fontSize: 11, color: '#6b6480', marginBottom: 8 }}>Provider & 模型</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <select
                value={provider}
                onChange={e => {
                  const p = e.target.value as AIProvider;
                  setProvider(p);
                  setModel(DEFAULT_MODELS[p]);
                }}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6,
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                  fontSize: 12, outline: 'none',
                }}
              >
                <option value="claude">Claude</option>
                <option value="openai">OpenAI</option>
              </select>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                style={{
                  flex: 1, padding: '8px 12px', borderRadius: 6,
                  border: '1px solid rgba(255,255,255,0.08)',
                  background: 'rgba(255,255,255,0.04)', color: '#f0e8da',
                  fontSize: 12, outline: 'none',
                }}
              >
                {PROVIDER_MODELS[provider].map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={!selectedNote || status === 'loading'}
        style={{
          padding: '12px 24px', borderRadius: 10, border: 'none',
          background: status === 'loading' ? 'rgba(240,192,64,0.3)' : 'linear-gradient(135deg, #f0c040, #c99f2e)',
          color: status === 'loading' ? '#a8a0b8' : '#0a0e1a',
          fontSize: 14, fontWeight: 700, cursor: status === 'loading' ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          opacity: !selectedNote ? 0.5 : 1,
        }}
      >
        {status === 'loading' ? (
          <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> 正在分析...</>
        ) : (
          <><Play size={18} /> 运行 Agent</>
        )}
      </button>

      {/* Error state */}
      <AnimatePresence>
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="glass"
            style={{
              padding: 16, borderRadius: 10,
              border: '1px solid rgba(231,76,60,0.2)',
              background: 'rgba(231,76,60,0.06)',
              display: 'flex', alignItems: 'flex-start', gap: 10,
            }}
          >
            <AlertCircle size={18} color="#e74c3c" style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontSize: 12, color: '#e74c3c', fontWeight: 600, marginBottom: 4 }}>运行失败</div>
              <div style={{ fontSize: 12, color: '#a8a0b8', whiteSpace: 'pre-wrap' }}>{error}</div>
              <button
                onClick={handleRun}
                style={{ marginTop: 8, padding: '4px 12px', borderRadius: 6, border: '1px solid rgba(231,76,60,0.3)', background: 'none', color: '#e74c3c', fontSize: 11, cursor: 'pointer' }}
              >
                重试
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Result display */}
      <AnimatePresence mode="wait">
        {status === 'loading' && (
          <motion.div
            key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 12,
              color: '#6b6480',
            }}
          >
            <Loader2 size={32} style={{ animation: 'spin 1s linear infinite' }} />
            <div style={{ fontSize: 13 }}>
              正在使用 {PROVIDER_LABELS[provider]} {model} 处理笔记...
            </div>
          </motion.div>
        )}

        {status === 'success' && result && (
          <motion.div
            key="result" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="glass"
            style={{
              flex: 1, padding: 20, borderRadius: 12,
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle size={16} color="#27ae60" />
                <span style={{ fontSize: 13, color: '#27ae60', fontWeight: 600 }}>分析完成</span>
                <span style={{ fontSize: 11, color: '#6b6480' }}>
                  ({result.provider} / {result.model})
                </span>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={handleCopyResult} style={iconBtnStyle} title="复制结果">
                  <Copy size={14} />
                </button>
              </div>
            </div>
            <div
              style={{
                flex: 1, overflow: 'auto', fontSize: 13, lineHeight: 1.7,
                color: '#d0c8d8',
              }}
            >
              <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', margin: 0 }}>
                {result.content}
              </pre>
            </div>
          </motion.div>
        )}

        {status === 'idle' && (
          <motion.div
            key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            style={{
              flex: 1, display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center', gap: 12,
              color: '#6b6480',
            }}
          >
            <Sparkles size={32} opacity={0.3} />
            <div style={{ fontSize: 13 }}>选择笔记和 Agent 后开始分析</div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

const iconBtnStyle: React.CSSProperties = {
  padding: '6px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.08)',
  background: 'rgba(255,255,255,0.04)', color: '#a8a0b8',
  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
};
```

- [ ] **Step 2: 提交**

```bash
git add app/src/components/AgentPanel.tsx
git commit -m "feat: 创建 AgentPanel 组件（Agent 选择/笔记选择/结果展示）"
```

---

### Task 7: 集成 Agent 标签页到知识库

**Files:**
- Modify: `app/src/pages/KnowledgePage.tsx`

- [ ] **Step 1: 在 KnowledgePage 中添加 Agent 标签页**

Edit `app/src/pages/KnowledgePage.tsx`, find the line:
```tsx
type Tab = 'browse' | 'graph' | 'analysis';
```
Change to:
```tsx
type Tab = 'browse' | 'graph' | 'analysis' | 'agent';
```

Then find the tab buttons array:
```tsx
{[
  { key: 'browse' as Tab, label: '浏览', icon: Search },
  { key: 'graph' as Tab, label: '知识图谱', icon: Network },
  { key: 'analysis' as Tab, label: '链接分析', icon: BarChart3 },
].map(t => ( ... )}
```
Add a 4th tab entry:
```tsx
{ key: 'agent' as Tab, label: 'AI Agent', icon: Sparkles },
```

Import `Sparkles` from lucide-react (add to existing imports):
```tsx
import { ..., Sparkles } from 'lucide-react';
```

Import AgentPanel:
```tsx
import AgentPanel from '../components/AgentPanel';
```

Add the agent tab content after the `analysis` tab's closing `</motion.div>`:
```tsx
{tab === 'agent' && (
  <motion.div
    key="agent" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
    style={{ height: '100%', overflow: 'auto' }}
  >
    <AgentPanel notes={notes} />
  </motion.div>
)}
```

- [ ] **Step 2: 验证前端编译**

Run: `cd app && npx tsc --noEmit 2>&1 | head -30`
Expected: 编译成功，无类型错误

- [ ] **Step 3: 提交**

```bash
git add app/src/pages/KnowledgePage.tsx
git commit -m "feat: 在知识库页面集成 AI Agent 标签页"
```

---

## 验证清单

- [ ] `cd app && cargo check` — Rust 编译通过
- [ ] `cd app && npx tsc --noEmit` — TypeScript 类型检查通过
- [ ] `cd app && npm run build` — 完整构建通过
- [ ] 应用启动后，知识库页面出现"AI Agent"标签页
- [ ] 配置 Claude API Key 后，运行"笔记整理"Agent 能正常返回结果
- [ ] 选择 OpenAI 后，运行"知识点提取"Agent 能正常返回结果
- [ ] 笔记内容为空时，运行按钮被禁用
- [ ] 未配置 API Key 时，运行返回友好提示
- [ ] API 请求失败时，显示错误信息和重试按钮
- [ ] 复制结果功能可用
