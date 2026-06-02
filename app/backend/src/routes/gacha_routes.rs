use actix_web::{web, HttpResponse, get, post};
use rusqlite::params;

use crate::models::task::{ApiResponse, Task};
use crate::models::gacha::*;
use crate::services::{task_service, gacha_service};
use crate::db;

// ===== Shared DB =====
fn db(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

// ===== DRAW /api/gacha/draw =====
#[post("/api/gacha/draw")]
pub async fn draw(
    state: web::Data<crate::AppState>,
    body: web::Json<DrawRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let energy = body.current_energy.as_deref().unwrap_or("medium");
    let (lo, hi) = gacha_service::pool_time_range(&body.pool);

    // Get available tasks matching time range
    let sql = "SELECT * FROM tasks WHERE completed = 0 AND in_discard_pile = 0 AND is_unlocked = 1
               AND estimated_time >= ?1 AND estimated_time < ?2
               AND task_profile != 'daily_habit'
               ORDER BY priority DESC";

    let mut stmt = match conn.prepare(sql) {
        Ok(s) => s,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询失败: {}", e))),
    };

    let rows = stmt.query_map(params![lo, hi], |row| {
        let id: i64 = row.get("id")?;
        let tags = db::get_task_tags(&conn, id).unwrap_or_default();
        Task::from_row(row, tags)
    });

    let mut tasks: Vec<Task> = match rows {
        Ok(r) => r.filter_map(|r| r.ok()).collect(),
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("读取失败: {}", e))),
    };

    // Fallback: if no tasks in range, use all available
    if tasks.is_empty() {
        let mut stmt = match conn.prepare(
            "SELECT * FROM tasks WHERE completed = 0 AND in_discard_pile = 0 AND is_unlocked = 1 AND task_profile != 'daily_habit'"
        ) {
            Ok(s) => s,
            Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询失败: {}", e))),
        };
        let rows = stmt.query_map([], |row| {
            let id: i64 = row.get("id")?;
            let tags = db::get_task_tags(&conn, id).unwrap_or_default();
            Task::from_row(row, tags)
        });
        tasks = match rows {
            Ok(r) => r.filter_map(|r| r.ok()).collect(),
            Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("读取失败: {}", e))),
        };
    }

    // Filter by specific task IDs if provided
    if let Some(ref ids) = body.available_task_ids {
        tasks.retain(|t| t.id.map(|id| ids.contains(&id)).unwrap_or(false));
    }

    // Get top-3 weighted
    let choices = task_service::get_top_weighted(&tasks, 3, energy);

    if choices.is_empty() {
        return HttpResponse::Ok().json(ApiResponse::ok(DrawChoiceResult {
            pool: body.pool.clone(),
            choices: vec![],
            slot_index: 0,
            is_urgent: false,
        }));
    }

    let is_urgent = choices[0].deadline.as_ref().map_or(false, |d| {
        chrono::DateTime::parse_from_rfc3339(d).ok()
            .map(|dt| {
                let dt_utc = dt.with_timezone(&chrono::Utc);
                (chrono::Utc::now() - dt_utc).num_days() >= -1
            })
            .unwrap_or(false)
    });

    HttpResponse::Ok().json(ApiResponse::ok(DrawChoiceResult {
        pool: body.pool.clone(),
        choices,
        slot_index: 0,
        is_urgent,
    }))
}

// ===== PLAN /api/gacha/plan =====
#[post("/api/gacha/plan")]
pub async fn plan_draw(
    body: web::Json<PlanDrawRequest>,
) -> HttpResponse {
    let plans = gacha_service::plan_multi_draw(body.total_minutes);

    let suggestions: Vec<String> = plans.iter().map(|p| {
        let name = match p.pool.as_str() {
            "fragment" => "碎片卡池",
            "tomato" => "番茄卡池",
            "deep" => "深度卡池",
            _ => "未知",
        };
        let time = match p.pool.as_str() {
            "fragment" => "~10 分钟",
            "tomato" => "25 分钟",
            "deep" => "50 分钟",
            _ => "",
        };
        format!("{} × {}（每段 {}）", name, p.count, time)
    }).collect();

    HttpResponse::Ok().json(serde_json::json!({
        "success": true,
        "data": {
            "plans": plans,
            "suggestions": suggestions
        }
    }))
}

// ===== ACCEPT /api/gacha/accept =====
#[post("/api/gacha/accept")]
pub async fn accept_draw(
    state: web::Data<crate::AppState>,
    body: web::Json<AcceptDrawRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let now = Task::now_iso();

    conn.execute(
        "INSERT INTO gacha_records (timestamp, pool_name, available_time, task_id, accepted)
         VALUES (?1, ?2, ?3, ?4, 1)",
        params![now, body.pool_name, body.available_time, body.task_id],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("记录失败: {}", e))))
}

// ===== REJECT /api/gacha/reject =====
#[post("/api/gacha/reject")]
pub async fn reject_draw(
    state: web::Data<crate::AppState>,
    body: web::Json<RejectDrawRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let now = Task::now_iso();

    // Record rejection
    if let Err(e) = conn.execute(
        "INSERT INTO task_rejection_log (task_id, reason, timestamp) VALUES (?1, ?2, ?3)",
        params![body.task_id, body.reason, now],
    ) {
        return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("记录拒绝失败: {}", e)));
    }

    // Increment refusal count
    let _ = conn.execute(
        "UPDATE tasks SET refusal_count = refusal_count + 1 WHERE id = ?1",
        params![body.task_id],
    );

    HttpResponse::Ok().json(ApiResponse::ok(true))
}

// ===== RECORDS /api/gacha/records =====
#[get("/api/gacha/records")]
pub async fn list_records(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    let mut stmt = match conn.prepare("SELECT * FROM gacha_records ORDER BY timestamp DESC LIMIT 100") {
        Ok(s) => s,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询失败: {}", e))),
    };

    let records: Vec<GachaRecord> = stmt.query_map([], |row| {
        Ok(GachaRecord {
            id: Some(row.get("id")?),
            timestamp: row.get("timestamp")?,
            pool_name: row.get("pool_name")?,
            available_time: row.get("available_time")?,
            task_id: row.get("task_id")?,
            accepted: row.get::<_, i64>("accepted")? != 0,
            refusal_reason: row.get("refusal_reason")?,
        })
    }).unwrap().filter_map(|r| r.ok()).collect();

    HttpResponse::Ok().json(ApiResponse::ok(records))
}

// ===== REJECTIONS /api/gacha/rejections =====
#[get("/api/gacha/rejections")]
pub async fn list_rejections(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    let mut stmt = match conn.prepare("SELECT * FROM task_rejection_log ORDER BY timestamp DESC LIMIT 100") {
        Ok(s) => s,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询失败: {}", e))),
    };

    let records: Vec<TaskRejectionLog> = stmt.query_map([], |row| {
        Ok(TaskRejectionLog {
            id: Some(row.get("id")?),
            task_id: row.get("task_id")?,
            reason: row.get("reason")?,
            timestamp: row.get("timestamp")?,
        })
    }).unwrap().filter_map(|r| r.ok()).collect();

    HttpResponse::Ok().json(ApiResponse::ok(records))
}
