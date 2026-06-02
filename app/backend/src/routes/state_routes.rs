use actix_web::{web, HttpResponse, get, post};
use rusqlite::params;

use crate::models::task::ApiResponse;
use crate::models::state::*;

fn db(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

// ===== GET /api/daily/state/{date} =====
#[get("/api/daily/state/{date}")]
pub async fn get_daily_state(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let date = path.into_inner();

    match conn.query_row(
        "SELECT * FROM daily_user_state WHERE date = ?1",
        params![date],
        |row| {
            Ok(DailyUserState {
                id: Some(row.get("id")?),
                date: row.get("date")?,
                daily_tone: row.get("daily_tone")?,
                energy_morning: row.get("energy_morning")?,
                energy_afternoon: row.get("energy_afternoon")?,
                energy_evening: row.get("energy_evening")?,
                bed_time: row.get("bed_time")?,
                sleep_early_streak: row.get("sleep_early_streak")?,
            })
        },
    ) {
        Ok(s) => HttpResponse::Ok().json(ApiResponse::ok(s)),
        Err(_) => HttpResponse::Ok().json(ApiResponse::ok(DailyUserState {
            id: None,
            date: date.clone(),
            daily_tone: "normal".into(),
            energy_morning: None,
            energy_afternoon: None,
            energy_evening: None,
            bed_time: None,
            sleep_early_streak: 0,
        })),
    }
}

// ===== POST /api/daily/state =====
#[post("/api/daily/state")]
pub async fn set_daily_state(
    state: web::Data<crate::AppState>,
    body: web::Json<SetDailyStateRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let tone = body.daily_tone.as_deref().unwrap_or("normal");

    conn.execute(
        "INSERT OR REPLACE INTO daily_user_state (date, daily_tone, energy_morning, energy_afternoon, energy_evening)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![body.date, tone, body.energy_morning, body.energy_afternoon, body.energy_evening],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("保存失败: {}", e))))
}

// ===== POST /api/daily/sleep =====
#[post("/api/daily/sleep")]
pub async fn record_sleep(
    state: web::Data<crate::AppState>,
    body: web::Json<RecordSleepRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    let existing_streak: i64 = conn.query_row(
        "SELECT sleep_early_streak FROM daily_user_state WHERE date = ?1",
        params![body.date],
        |row| row.get(0),
    ).unwrap_or(0);

    let new_streak = if body.on_time { existing_streak + 1 } else { 0 };

    conn.execute(
        "INSERT OR REPLACE INTO daily_user_state (date, daily_tone, bed_time, sleep_early_streak)
         VALUES (?1, COALESCE((SELECT daily_tone FROM daily_user_state WHERE date = ?1), 'normal'), ?2, ?3)",
        params![body.date, body.bed_time, new_streak],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("记录睡眠失败: {}", e))))
}
