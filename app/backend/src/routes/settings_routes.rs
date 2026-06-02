use actix_web::{web, HttpResponse, get, put};
use rusqlite::params;

use crate::models::task::ApiResponse;

fn db(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

fn default_settings_json() -> &'static str {
    r##"{"llm":{"apiUrl":"","apiKey":"","modelName":"gpt-4o"},"mineru":{"apiUrl":"","apiKey":""},"theme":{"primaryColor":"#f5e6a0","primaryColorLight":"#fdf6d4","primaryColorDark":"#d4c06a","themeMode":"light"}}"##
}

// ===== GET /api/settings =====
#[get("/api/settings")]
pub async fn get_settings(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    let json_str: String = conn.query_row(
        "SELECT value FROM settings WHERE id = 1",
        [],
        |row| row.get(0),
    ).unwrap_or_else(|_| default_settings_json().to_string());

    match serde_json::from_str::<serde_json::Value>(&json_str) {
        Ok(val) => HttpResponse::Ok().json(ApiResponse::ok(val)),
        Err(_) => {
            // If JSON is corrupted, reset to default
            let _ = conn.execute(
                "INSERT OR REPLACE INTO settings (id, value) VALUES (1, ?1)",
                params![default_settings_json()],
            );
            let default: serde_json::Value = serde_json::from_str(default_settings_json()).unwrap();
            HttpResponse::Ok().json(ApiResponse::ok(default))
        }
    }
}

// ===== PUT /api/settings =====
#[put("/api/settings")]
pub async fn update_settings(
    state: web::Data<crate::AppState>,
    body: web::Json<serde_json::Value>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let json_str = serde_json::to_string(&body.0).unwrap_or_else(|_| default_settings_json().to_string());

    conn.execute(
        "INSERT OR REPLACE INTO settings (id, value) VALUES (1, ?1)",
        params![json_str],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("保存设置失败: {}", e))))
}

// ===== PUT /api/settings/reset =====
#[put("/api/settings/reset")]
pub async fn reset_settings(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    conn.execute(
        "INSERT OR REPLACE INTO settings (id, value) VALUES (1, ?1)",
        params![default_settings_json()],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("重置设置失败: {}", e))))
}
