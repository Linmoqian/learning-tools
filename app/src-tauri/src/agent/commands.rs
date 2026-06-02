use super::api_client::{self, AgentResult};
use super::key_manager;
use super::prompts;
use tauri::Emitter;
use tauri::Manager;

#[derive(serde::Deserialize)]
#[serde(rename_all = "camelCase")]
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
pub async fn run_agent_stream(
    app: tauri::AppHandle,
    request: RunAgentRequest,
) -> Result<(), String> {
    let agent_type = &request.agent_type;
    let note_content = &request.note_content;
    let provider = request.provider.as_deref().unwrap_or("claude");

    if note_content.trim().is_empty() {
        let _ = app.emit("agent-error", api_client::ErrorPayload {
            message: "笔记内容不能为空".to_string(),
        });
        return Err("笔记内容不能为空".to_string());
    }

    // Get prompt
    let prompt = prompts::get_prompt(agent_type)
        .ok_or_else(|| {
            let msg = format!("未知的 Agent 类型: {}", agent_type);
            let _ = app.emit("agent-error", api_client::ErrorPayload { message: msg.clone() });
            msg
        })?;

    // Get API key
    let app_data_dir = app.path().app_data_dir()
        .map_err(|e| format!("获取应用数据目录失败: {}", e))?;

    let api_key = key_manager::get_key(&app_data_dir, provider)
        .ok_or_else(|| {
            let msg = format!("{} API Key 未配置，请到设置中配置", provider);
            let _ = app.emit("agent-error", api_client::ErrorPayload { message: msg.clone() });
            msg
        })?;

    // Resolve model
    let resolved_model = match request.model.as_deref().unwrap_or("") {
        "" => match provider {
            "claude" => "claude-sonnet-4-20250514",
            "openai" => "gpt-4o",
            _ => return Err(format!("未知的 provider: {}", provider)),
        },
        m => m,
    };

    // Call streaming API
    match provider {
        "claude" => api_client::call_claude_stream(&app, &api_key, resolved_model, prompt, note_content).await,
        "openai" => api_client::call_openai_stream(&app, &api_key, resolved_model, prompt, note_content).await,
        _ => Err(format!("未知的 provider: {}", provider)),
    }
}
