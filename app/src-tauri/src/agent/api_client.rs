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
        .header("anthropic-version", "2024-10-01")
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
        let truncated = if body.len() > 200 { format!("{}...（共{}字符）", &body[..200], body.len()) } else { body.clone() };
        return Err(format!("Claude API 返回错误 ({}): {}", status.as_u16(), truncated));
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
        let truncated = if body.len() > 200 { format!("{}...（共{}字符）", &body[..200], body.len()) } else { body.clone() };
        return Err(format!("OpenAI API 返回错误 ({}): {}", status.as_u16(), truncated));
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
