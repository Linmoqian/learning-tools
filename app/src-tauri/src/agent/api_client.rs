use futures::StreamExt;
use serde::{Deserialize, Serialize};
use tauri::Emitter;

#[derive(Debug, Serialize, Deserialize)]
pub struct AgentResult {
    pub content: String,
    pub model: String,
    pub provider: String,
}

// ===== Streaming events payloads =====

#[derive(Debug, Serialize, Clone)]
pub struct TokenPayload {
    pub token: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct DonePayload {
    pub content: String,
    pub model: String,
    pub provider: String,
}

#[derive(Debug, Serialize, Clone)]
pub struct ErrorPayload {
    pub message: String,
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

// ===== Streaming API =====

pub async fn call_claude_stream(
    app_handle: &tauri::AppHandle,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_content: &str,
) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(180))
        .build()
        .map_err(|e| format!("创建 HTTP 客户端失败: {}", e))?;

    let body = serde_json::json!({
        "model": model,
        "max_tokens": 4096,
        "stream": true,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_content}
        ]
    });

    let response = client
        .post("https://api.anthropic.com/v1/messages")
        .header("x-api-key", api_key)
        .header("anthropic-version", "2024-10-01")
        .header("content-type", "application/json")
        .json(&body)
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                "API 请求超时".to_string()
            } else if e.is_connect() {
                format!("网络连接失败: {}", e)
            } else {
                format!("API 请求失败: {}", e)
            }
        })?;

    let status = response.status();
    if !status.is_success() {
        let err_body = response.text().await.unwrap_or_default();
        let truncated = if err_body.len() > 200 {
            format!("{}...（共{}字符）", &err_body[..200], err_body.len())
        } else {
            err_body
        };
        return Err(format!("Claude API 返回错误 ({}): {}", status.as_u16(), truncated));
    }

    // Stream SSE
    let mut stream = response.bytes_stream();
    let mut buffer = String::new();
    let mut current_event = String::new();
    let mut full_content = String::new();
    let mut full_thinking = String::new();
    let mut last_model = model.to_string();

    while let Some(chunk_result) = stream.next().await {
        let chunk = chunk_result.map_err(|e| format!("读取流失败: {}", e))?;
        let chunk_str = String::from_utf8_lossy(&chunk);
        buffer.push_str(&chunk_str);

        // Process complete lines
        loop {
            let newline_pos = match buffer.find('\n') {
                Some(pos) => pos,
                None => break,
            };
            let line = buffer[..newline_pos].to_string();
            buffer = buffer[newline_pos + 1..].to_string();

            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            if let Some(event_name) = trimmed.strip_prefix("event: ") {
                current_event = event_name.to_string();
            } else if let Some(data_str) = trimmed.strip_prefix("data: ") {
                match current_event.as_str() {
                    "content_block_delta" => {
                        if let Ok(data) = serde_json::from_str::<serde_json::Value>(data_str) {
                            if let Some(delta) = data.get("delta") {
                                if let Some(text) = delta.get("text").and_then(|v| v.as_str()) {
                                    full_content.push_str(text);
                                    let _ = app_handle.emit("agent-token", TokenPayload { token: text.to_string() });
                                }
                                if let Some(thinking) = delta.get("thinking").and_then(|v| v.as_str()) {
                                    full_thinking.push_str(thinking);
                                    let _ = app_handle.emit("agent-thinking", TokenPayload { token: thinking.to_string() });
                                }
                            }
                        }
                    }
                    "message_start" => {
                        if let Ok(data) = serde_json::from_str::<serde_json::Value>(data_str) {
                            if let Some(msg) = data.get("message") {
                                if let Some(m) = msg.get("model").and_then(|v| v.as_str()) {
                                    last_model = m.to_string();
                                }
                            }
                        }
                    }
                    "message_stop" => {
                        let _ = app_handle.emit("agent-done", DonePayload {
                            content: full_content.clone(),
                            model: last_model.clone(),
                            provider: "claude".to_string(),
                        });
                        return Ok(());
                    }
                    "error" => {
                        let err_msg = serde_json::from_str::<serde_json::Value>(data_str)
                            .ok()
                            .and_then(|v| {
                                v.get("error")
                                    .and_then(|e| e.get("message"))
                                    .and_then(|m| m.as_str().map(|s| s.to_string()))
                            })
                            .unwrap_or_else(|| "未知错误".to_string());
                        let _ = app_handle.emit("agent-error", ErrorPayload { message: err_msg.clone() });
                        return Err(err_msg);
                    }
                    _ => {}
                }
            }
        }
    }

    // Stream ended without message_stop — emit done with whatever we have
    let _ = app_handle.emit("agent-done", DonePayload {
        content: full_content,
        model: last_model,
        provider: "claude".to_string(),
    });
    Ok(())
}

pub async fn call_openai_stream(
    app_handle: &tauri::AppHandle,
    api_key: &str,
    model: &str,
    system_prompt: &str,
    user_content: &str,
) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(180))
        .build()
        .map_err(|e| format!("创建 HTTP 客户端失败: {}", e))?;

    let body = serde_json::json!({
        "model": model,
        "max_tokens": 4096,
        "stream": true,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    });

    let response = client
        .post("https://api.openai.com/v1/chat/completions")
        .header("Authorization", format!("Bearer {}", api_key))
        .header("content-type", "application/json")
        .json(&body)
        .send()
        .await
        .map_err(|e| {
            if e.is_timeout() {
                "API 请求超时".to_string()
            } else if e.is_connect() {
                format!("网络连接失败: {}", e)
            } else {
                format!("API 请求失败: {}", e)
            }
        })?;

    let status = response.status();
    if !status.is_success() {
        let err_body = response.text().await.unwrap_or_default();
        let truncated = if err_body.len() > 200 {
            format!("{}...（共{}字符）", &err_body[..200], err_body.len())
        } else {
            err_body
        };
        return Err(format!("OpenAI API 返回错误 ({}): {}", status.as_u16(), truncated));
    }

    // Stream SSE
    let mut stream = response.bytes_stream();
    let mut buffer = String::new();
    let mut full_content = String::new();
    let mut last_model = model.to_string();

    while let Some(chunk_result) = stream.next().await {
        let chunk = chunk_result.map_err(|e| format!("读取流失败: {}", e))?;
        let chunk_str = String::from_utf8_lossy(&chunk);
        buffer.push_str(&chunk_str);

        loop {
            let newline_pos = match buffer.find('\n') {
                Some(pos) => pos,
                None => break,
            };
            let line = buffer[..newline_pos].to_string();
            buffer = buffer[newline_pos + 1..].to_string();

            let trimmed = line.trim();
            if trimmed.is_empty() {
                continue;
            }

            if let Some(data_str) = trimmed.strip_prefix("data: ") {
                let data_str = data_str.trim();
                if data_str == "[DONE]" {
                    let _ = app_handle.emit("agent-done", DonePayload {
                        content: full_content.clone(),
                        model: last_model.clone(),
                        provider: "openai".to_string(),
                    });
                    return Ok(());
                }

                if let Ok(data) = serde_json::from_str::<serde_json::Value>(data_str) {
                    if let Some(choices) = data.get("choices").and_then(|v| v.as_array()) {
                        if let Some(choice) = choices.first() {
                            if let Some(delta) = choice.get("delta") {
                                if let Some(content) = delta.get("content").and_then(|v| v.as_str()) {
                                    full_content.push_str(content);
                                    let _ = app_handle.emit("agent-token", TokenPayload { token: content.to_string() });
                                }
                            }
                            if let Some(finish_reason) = choice.get("finish_reason").and_then(|v| v.as_str()) {
                                if !finish_reason.is_empty() && finish_reason != "null" {
                                    let _ = app_handle.emit("agent-done", DonePayload {
                                        content: full_content.clone(),
                                        model: last_model.clone(),
                                        provider: "openai".to_string(),
                                    });
                                    return Ok(());
                                }
                            }
                        }
                    }
                    // Capture model name from first chunk
                    if let Some(m) = data.get("model").and_then(|v| v.as_str()) {
                        if last_model == model {
                            last_model = m.to_string();
                        }
                    }
                }
            }
        }
    }

    // Stream ended without [DONE]
    let _ = app_handle.emit("agent-done", DonePayload {
        content: full_content,
        model: last_model,
        provider: "openai".to_string(),
    });
    Ok(())
}
