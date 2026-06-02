use actix_web::{web, HttpResponse, get, post, delete};
use rusqlite::params;

use crate::models::task::ApiResponse;
use crate::models::schedule::*;
use crate::db;

fn db_conn(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

// ===== SLOTS /api/schedule/slots =====
#[get("/api/schedule/slots")]
pub async fn get_slots() -> HttpResponse {
    HttpResponse::Ok().json(ApiResponse::ok(default_slots()))
}

// ===== GET /api/schedule/{date} =====
#[get("/api/schedule/{date}")]
pub async fn get_day_schedule(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let date = path.into_inner();

    // Daily schedule items
    let mut stmt = conn.prepare(
        "SELECT * FROM daily_schedules WHERE date = ?1 ORDER BY time_slot"
    ).unwrap();
    let items: Vec<ScheduleItem> = stmt.query_map(params![date], |row| {
        Ok(ScheduleItem {
            id: Some(row.get("id")?),
            date: row.get("date")?,
            slot_id: row.get("time_slot")?,
            activity: row.get("activity")?,
            notes: Some(row.get::<_, String>("notes").unwrap_or_default()),
            schedule_type: "temporary".into(),
            day_of_week: None,
        })
    }).unwrap().filter_map(|r| r.ok()).collect();

    // Weekly templates
    let day_of_week = match chrono::NaiveDate::parse_from_str(&date, "%Y-%m-%d") {
        Ok(d) => d.format("%u").to_string().parse::<i64>().unwrap_or(7),
        Err(_) => 7,
    };

    let mut wstmt = conn.prepare(
        "SELECT * FROM user_schedule WHERE day_of_week = ?1 AND is_regular = 1 ORDER BY time_slot"
    ).unwrap();
    let weekly: Vec<ScheduleItem> = wstmt.query_map(params![day_of_week], |row| {
        Ok(ScheduleItem {
            id: Some(row.get("id")?),
            date: date.clone(),
            slot_id: row.get("time_slot")?,
            activity: row.get("activity")?,
            notes: Some(row.get::<_, String>("notes").unwrap_or_default()),
            schedule_type: "weekly".into(),
            day_of_week: Some(day_of_week),
        })
    }).unwrap().filter_map(|r| r.ok()).collect();

    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "data": {
            "date": date,
            "items": items,
            "weeklyTemplates": weekly
        }
    }))
}

// ===== SET /api/schedule =====
#[post("/api/schedule")]
pub async fn set_schedule(
    state: web::Data<crate::AppState>,
    body: web::Json<SetScheduleRequest>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let stype = body.schedule_type.as_deref().unwrap_or("temporary");

    match stype {
        "weekly" => {
            let dow = body.day_of_week.unwrap_or(1);
            if let Err(e) = conn.execute(
                "INSERT OR REPLACE INTO user_schedule (day_of_week, time_slot, activity, notes, is_regular) VALUES (?1, ?2, ?3, ?4, 1)",
                params![dow, body.slot_id, body.activity, body.notes.as_deref().unwrap_or("")],
            ) {
                return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("设置失败: {}", e)));
            }
            let _ = conn.execute("INSERT OR IGNORE INTO activities (name) VALUES (?1)", params![body.activity]);
        }
        _ => {
            if let Err(e) = conn.execute(
                "INSERT OR REPLACE INTO daily_schedules (date, time_slot, activity, notes) VALUES (?1, ?2, ?3, ?4)",
                params![body.date, body.slot_id, body.activity, body.notes.as_deref().unwrap_or("")],
            ) {
                return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("设置失败: {}", e)));
            }
        }
    }

    HttpResponse::Ok().json(ApiResponse::ok(true))
}

// ===== DELETE /api/schedule/{date}/{slot_id} =====
#[delete("/api/schedule/{date}/{slot_id}")]
pub async fn delete_schedule(
    state: web::Data<crate::AppState>,
    path: web::Path<(String, String)>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let (date, slot_id) = path.into_inner();

    conn.execute(
        "DELETE FROM daily_schedules WHERE date = ?1 AND time_slot = ?2",
        params![date, slot_id],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("删除失败: {}", e))))
}

// ===== GET /api/schedule/weekly/{day} =====
#[get("/api/schedule/weekly/{day}")]
pub async fn get_weekly(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let day = path.into_inner();

    let mut stmt = conn.prepare(
        "SELECT time_slot, activity, notes FROM user_schedule WHERE day_of_week = ?1 AND is_regular = 1 ORDER BY time_slot"
    ).unwrap();

    let items: Vec<ScheduleItem> = stmt.query_map(params![day], |row| {
        Ok(ScheduleItem {
            id: None,
            date: String::new(),
            slot_id: row.get("time_slot")?,
            activity: row.get("activity")?,
            notes: Some(row.get::<_, String>("notes").unwrap_or_default()),
            schedule_type: "weekly".into(),
            day_of_week: Some(day),
        })
    }).unwrap().filter_map(|r| r.ok()).collect();

    HttpResponse::Ok().json(ApiResponse::ok(items))
}

// ===== ACTIVITIES =====

#[get("/api/activities")]
pub async fn list_activities(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let mut stmt = conn.prepare("SELECT name FROM activities ORDER BY name").unwrap();
    let activities: Vec<String> = stmt.query_map([], |row| row.get(0))
        .unwrap().filter_map(|r| r.ok()).collect();
    HttpResponse::Ok().json(ApiResponse::ok(activities))
}

#[post("/api/activities")]
pub async fn create_activity(
    state: web::Data<crate::AppState>,
    body: web::Json<serde_json::Value>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let name = body.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
    if name.is_empty() {
        return HttpResponse::BadRequest().json(ApiResponse::<()>::err("活动名不能为空"));
    }
    let _ = conn.execute("INSERT OR IGNORE INTO activities (name) VALUES (?1)", params![name]);
    HttpResponse::Ok().json(ApiResponse::ok(true))
}

#[delete("/api/activities/{name}")]
pub async fn delete_activity(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let name = path.into_inner();
    conn.execute("DELETE FROM activities WHERE name = ?1", params![name])
        .map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
        .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("删除失败: {}", e))))
}
