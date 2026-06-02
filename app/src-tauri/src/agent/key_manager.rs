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
    let content = match std::fs::read_to_string(&path) {
        Ok(c) => c,
        Err(_) => return ApiKeys::default(),
    };
    serde_json::from_str(&content).unwrap_or_default()
}

pub fn get_key_status(app_data_dir: &PathBuf) -> (bool, bool) {
    let keys = load_keys_internal(app_data_dir);
    (keys.claude.is_some(), keys.openai.is_some())
}
