use actix_web::{web, HttpResponse, get, post, put, delete};
use rusqlite::params;
use serde_json;

use crate::db;
use crate::models::task::*;
use crate::services::task_service;

// ===== Shared DB connection helper =====
fn db(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

fn opt_str(s: &Option<String>) -> String {
    s.as_deref().unwrap_or("").to_string()
}

// ===== LIST /api/tasks =====
#[get("/api/tasks")]
pub async fn list_tasks(
    state: web::Data<crate::AppState>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let search = query.get("search").cloned().unwrap_or_default();
    let tag = query.get("tag").cloned().unwrap_or_default();
    let completed = query.get("completed").and_then(|v| v.parse::<bool>().ok());
    let discard = query.get("inDiscardPile").and_then(|v| v.parse::<bool>().ok());

    let mut sql = String::from("SELECT * FROM tasks WHERE 1=1");
    let mut sql_params: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();

    if !search.is_empty() {
        sql.push_str(" AND (name LIKE ?1 OR ?1 = '')");
        sql_params.push(Box::new(format!("%{}%", search)));
    }
    if let Some(c) = completed {
        sql.push_str(&format!(" AND completed = {}", if c { 1 } else { 0 }));
    }
    if let Some(d) = discard {
        sql.push_str(&format!(" AND in_discard_pile = {}", if d { 1 } else { 0 }));
    }
    sql.push_str(" ORDER BY created_at DESC");

    let mut stmt = match conn.prepare(&sql) {
        Ok(s) => s,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询失败: {}", e))),
    };

    let param_refs: Vec<&dyn rusqlite::types::ToSql> = sql_params.iter().map(|p| p.as_ref()).collect();
    let rows = match stmt.query_map(param_refs.as_slice(), |row| {
        let id: i64 = row.get("id")?;
        let tags = db::get_task_tags(&conn, id).unwrap_or_default();
        Task::from_row(row, tags)
    }) {
        Ok(r) => r,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("读取失败: {}", e))),
    };

    let mut tasks: Vec<Task> = Vec::new();
    for r in rows {
        match r {
            Ok(t) => tasks.push(t),
            Err(e) => log::error!("行解析错误: {}", e),
        }
    }

    // Client-side tag filter
    if !tag.is_empty() {
        tasks.retain(|t| t.tags.contains(&tag));
    }

    HttpResponse::Ok().json(ApiResponse::ok(tasks))
}

// ===== CREATE /api/tasks =====
#[post("/api/tasks")]
pub async fn create_task(
    state: web::Data<crate::AppState>,
    body: web::Json<CreateTaskRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let now = Task::now_iso();
    let prereq_json = serde_json::to_string(&body.prerequisite_ids.clone().unwrap_or_default()).unwrap_or_else(|_| "[]".into());
    let is_unlocked = body.prerequisite_ids.as_ref().map(|p| p.is_empty()).unwrap_or(true) as i64;

    let result = conn.execute(
        "INSERT INTO tasks (name, category, task_type, description, estimated_time, preferred_time, deadline,
         resistance, energy_required, rarity, priority, repeat_type, task_profile, is_daily, completed,
         in_discard_pile, draw_count_today, min_push_time, prerequisite_ids, is_unlocked, created_at, updated_at)
         VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16,?17,?18,?19,?20,?21,?22)",
        params![
            body.name, body.category.as_deref().unwrap_or("daily"), "normal",
            opt_str(&body.description), body.estimated_time.unwrap_or(25),
            opt_str(&body.preferred_time), opt_str(&body.deadline),
            body.resistance.as_deref().unwrap_or("medium"),
            body.energy_required.as_deref().unwrap_or("medium"),
            "common", body.priority.unwrap_or(5),
            body.repeat_type.as_deref().unwrap_or("none"),
            body.task_profile.as_deref().unwrap_or("deadline_flexible"),
            0i64, 0i64, 0i64, 0i64, "20:00", prereq_json, is_unlocked, now, now,
        ],
    );

    match result {
        Ok(_) => {
            let task_id = conn.last_insert_rowid();
            if let Some(ref tags) = body.tags {
                let _ = db::set_task_tags(&conn, task_id, tags);
            }
            match conn.query_row("SELECT * FROM tasks WHERE id = ?1", params![task_id], |row| {
                let tags = db::get_task_tags(&conn, task_id).unwrap_or_default();
                Task::from_row(row, tags)
            }) {
                Ok(task) => HttpResponse::Ok().json(ApiResponse::ok(task)),
                Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("读取新任务失败: {}", e))),
            }
        }
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("创建失败: {}", e))),
    }
}

// ===== GET /api/tasks/{id} =====
#[get("/api/tasks/{id}")]
pub async fn get_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();

    match conn.query_row("SELECT * FROM tasks WHERE id = ?1", params![task_id], |row| {
        let tags = db::get_task_tags(&conn, task_id).unwrap_or_default();
        Task::from_row(row, tags)
    }) {
        Ok(task) => HttpResponse::Ok().json(ApiResponse::ok(task)),
        Err(_) => HttpResponse::NotFound().json(ApiResponse::<()>::err("任务不存在")),
    }
}

// ===== UPDATE /api/tasks/{id} =====
#[put("/api/tasks/{id}")]
pub async fn update_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
    body: web::Json<UpdateTaskRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();

    let existing = match conn.query_row("SELECT * FROM tasks WHERE id = ?1", params![task_id], |row| {
        let tags = db::get_task_tags(&conn, task_id).unwrap_or_default();
        Task::from_row(row, tags)
    }) {
        Ok(t) => t,
        Err(_) => return HttpResponse::NotFound().json(ApiResponse::<()>::err("任务不存在")),
    };

    let mut sets = Vec::new();
    let mut vals: Vec<Box<dyn rusqlite::types::ToSql>> = Vec::new();

    macro_rules! set_field {
        ($field:literal, $opt:expr, $default:expr) => {
            if let Some(ref v) = $opt {
                sets.push(format!("{} = ?", $field));
                vals.push(Box::new(v.clone()) as Box<dyn rusqlite::types::ToSql>);
            }
        };
        ($field:literal, $opt:expr) => {
            if let Some(ref v) = $opt {
                sets.push(format!("{} = ?", $field));
                vals.push(Box::new(v.clone()) as Box<dyn rusqlite::types::ToSql>);
            }
        };
    }

    // Simple string fields
    set_field!("name", body.name);
    set_field!("category", body.category);
    set_field!("description", body.description);
    set_field!("estimated_time", body.estimated_time);
    set_field!("preferred_time", body.preferred_time);
    set_field!("deadline", body.deadline);
    set_field!("resistance", body.resistance);
    set_field!("energy_required", body.energy_required);
    set_field!("priority", body.priority);
    set_field!("repeat_type", body.repeat_type);
    set_field!("task_profile", body.task_profile);

    // Boolean-like fields
    if let Some(v) = body.completed {
        sets.push("completed = ?".into());
        vals.push(Box::new(if v { 1i64 } else { 0i64 }) as Box<dyn rusqlite::types::ToSql>);
    }
    if let Some(v) = body.in_discard_pile {
        sets.push("in_discard_pile = ?".into());
        vals.push(Box::new(if v { 1i64 } else { 0i64 }) as Box<dyn rusqlite::types::ToSql>);
    }
    if let Some(v) = body.is_unlocked {
        sets.push("is_unlocked = ?".into());
        vals.push(Box::new(if v { 1i64 } else { 0i64 }) as Box<dyn rusqlite::types::ToSql>);
    }

    // prerequisite_ids (JSON)
    if let Some(ref ids) = body.prerequisite_ids {
        let json = serde_json::to_string(ids).unwrap_or_else(|_| "[]".into());
        sets.push("prerequisite_ids = ?".into());
        vals.push(Box::new(json) as Box<dyn rusqlite::types::ToSql>);
    }

    if sets.is_empty() {
        return HttpResponse::Ok().json(ApiResponse::ok(existing));
    }

    let now = Task::now_iso();
    sets.push("updated_at = ?".into());
    vals.push(Box::new(now) as Box<dyn rusqlite::types::ToSql>);

    let sql = format!("UPDATE tasks SET {} WHERE id = ?", sets.join(", "));
    vals.push(Box::new(task_id) as Box<dyn rusqlite::types::ToSql>);

    let param_refs: Vec<&dyn rusqlite::types::ToSql> = vals.iter().map(|p| p.as_ref()).collect();
    if let Err(e) = conn.execute(&sql, param_refs.as_slice()) {
        return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("更新失败: {}", e)));
    }

    if let Some(ref tags) = body.tags {
        let _ = db::set_task_tags(&conn, task_id, tags);
    }

    match conn.query_row("SELECT * FROM tasks WHERE id = ?1", params![task_id], |row| {
        let tags = db::get_task_tags(&conn, task_id).unwrap_or_default();
        Task::from_row(row, tags)
    }) {
        Ok(task) => HttpResponse::Ok().json(ApiResponse::ok(task)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("读取更新结果失败: {}", e))),
    }
}

// ===== DELETE /api/tasks/{id} =====
#[delete("/api/tasks/{id}")]
pub async fn delete_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();

    match conn.execute("DELETE FROM tasks WHERE id = ?1", params![task_id]) {
        Ok(0) => HttpResponse::NotFound().json(ApiResponse::<()>::err("任务不存在")),
        Ok(_) => HttpResponse::Ok().json(ApiResponse::ok(true)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("删除失败: {}", e))),
    }
}

// ===== COMPLETE /api/tasks/{id}/complete =====
#[post("/api/tasks/{id}/complete")]
pub async fn complete_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
    body: web::Json<CompleteTaskRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();
    let now = Task::now_iso();

    if let Err(e) = conn.execute(
        "UPDATE tasks SET completed = 1, success_rate = MIN(1.0, success_rate + 0.1), updated_at = ?1 WHERE id = ?2",
        params![now, task_id],
    ) {
        return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("完成操作失败: {}", e)));
    }

    // Record feedback if provided
    if let Some(ref fb) = body.feedback {
        let _ = conn.execute(
            "INSERT INTO task_completion_feedback (task_id, energy_after, mood_after, timestamp) VALUES (?1, ?2, ?3, ?4)",
            params![task_id, fb.energy_after, fb.mood_after, now],
        );
    }

    // Chain unlock
    let (unlocked_names, unlocked_ids) = match task_service::chain_unlock(&conn, task_id) {
        Ok(r) => r,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("链式解锁失败: {}", e))),
    };

    HttpResponse::Ok().json(ApiResponse::ok(ChainUnlockResponse {
        unlocked_task_names: unlocked_names,
        unlocked_task_ids: unlocked_ids,
    }))
}

// ===== SKIP /api/tasks/{id}/skip =====
#[post("/api/tasks/{id}/skip")]
pub async fn skip_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();
    let now = Task::now_iso();

    if let Err(e) = conn.execute(
        "UPDATE tasks SET completed = 1, updated_at = ?1 WHERE id = ?2",
        params![now, task_id],
    ) {
        return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("跳过失败: {}", e)));
    }

    HttpResponse::Ok().json(ApiResponse::ok(true))
}

// ===== RECORD DRAW /api/tasks/{id}/draw =====
#[post("/api/tasks/{id}/draw")]
pub async fn record_draw(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();
    let now = Task::now_iso();

    if let Err(e) = conn.execute(
        "UPDATE tasks SET draw_count_today = draw_count_today + 1, last_drawn_at = ?1, updated_at = ?2 WHERE id = ?3",
        params![now, now, task_id],
    ) {
        return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("记录失败: {}", e)));
    }

    HttpResponse::Ok().json(ApiResponse::ok(true))
}

// ===== DISCARD /api/tasks/{id}/discard =====
#[post("/api/tasks/{id}/discard")]
pub async fn discard_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();
    let now = Task::now_iso();

    conn.execute(
        "UPDATE tasks SET in_discard_pile = 1, updated_at = ?1 WHERE id = ?2",
        params![now, task_id],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("移入弃牌堆失败: {}", e))))
}

// ===== RESTORE /api/tasks/{id}/restore =====
#[post("/api/tasks/{id}/restore")]
pub async fn restore_task(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let task_id = path.into_inner();
    let now = Task::now_iso();

    conn.execute(
        "UPDATE tasks SET in_discard_pile = 0, updated_at = ?1 WHERE id = ?2",
        params![now, task_id],
    ).map(|_| HttpResponse::Ok().json(ApiResponse::ok(true)))
    .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("恢复失败: {}", e))))
}

// ===== RESET DISCARD /api/tasks/reset-discard =====
#[post("/api/tasks/reset-discard")]
pub async fn reset_discard(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let now = Task::now_iso();

    match conn.execute("UPDATE tasks SET in_discard_pile = 0, updated_at = ?1 WHERE in_discard_pile = 1", params![now]) {
        Ok(n) => HttpResponse::Ok().json(ApiResponse::ok(n)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("重置弃牌堆失败: {}", e))),
    }
}

// ===== RESET PERIODIC /api/tasks/reset-periodic =====
#[post("/api/tasks/reset-periodic")]
pub async fn reset_periodic(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let now = Task::now_iso();

    // Reset draw count for all tasks
    let _ = conn.execute("UPDATE tasks SET draw_count_today = 0", []);

    // Daily repeat: un-complete and remove from discard
    conn.execute(
        "UPDATE tasks SET completed = 0, in_discard_pile = 0, next_available_at = NULL, updated_at = ?1
         WHERE repeat_type = 'daily' AND completed = 1",
        params![now],
    ).ok();

    // Weekly repeat: check next_available_at
    let weekly_ids: Vec<i64> = {
        let mut stmt = conn.prepare(
            "SELECT id FROM tasks WHERE repeat_type = 'weekly' AND completed = 1 AND next_available_at IS NOT NULL AND next_available_at <= ?1"
        ).unwrap();
        let rows = stmt.query_map(params![now], |row| row.get::<_, i64>(0)).unwrap();
        rows.filter_map(|r| r.ok()).collect()
    };

    for id in weekly_ids {
        conn.execute(
            "UPDATE tasks SET completed = 0, in_discard_pile = 0, next_available_at = NULL, updated_at = ?1 WHERE id = ?2",
            params![now, id],
        ).ok();
    }

    HttpResponse::Ok().json(ApiResponse::ok(true))
}

// ===== DETECT CYCLE /api/tasks/detect-cycle =====
#[post("/api/tasks/detect-cycle")]
pub async fn detect_cycle(
    state: web::Data<crate::AppState>,
    body: web::Json<DetectCycleRequest>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };

    match task_service::detect_cycle(&conn, body.task_id, &body.proposed_prerequisite_ids) {
        Ok(true) => HttpResponse::Ok().json(ApiResponse::ok(DetectCycleResponse {
            has_cycle: true,
            cycle_description: "检测到循环依赖".into(),
        })),
        Ok(false) => HttpResponse::Ok().json(ApiResponse::ok(DetectCycleResponse {
            has_cycle: false,
            cycle_description: "无循环依赖".into(),
        })),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("检测失败: {}", e))),
    }
}

// ===== TAG ROUTES =====

/// GET /api/tags
#[get("/api/tags")]
pub async fn list_tags(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let mut stmt = match conn.prepare("SELECT name FROM tags ORDER BY name") {
        Ok(s) => s,
        Err(e) => return HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("查询标签失败: {}", e))),
    };
    let tags: Vec<String> = stmt.query_map([], |row| row.get(0))
        .unwrap().filter_map(|r| r.ok()).collect();
    HttpResponse::Ok().json(ApiResponse::ok(tags))
}

/// POST /api/tags
#[post("/api/tags")]
pub async fn create_tag(
    state: web::Data<crate::AppState>,
    body: web::Json<serde_json::Value>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let name = body.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
    if name.is_empty() {
        return HttpResponse::BadRequest().json(ApiResponse::<()>::err("标签名不能为空"));
    }
    match conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?1)", params![name]) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::ok(true)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("创建标签失败: {}", e))),
    }
}

/// DELETE /api/tags/{name}
#[delete("/api/tags/{name}")]
pub async fn delete_tag(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let conn = match db(&state) { Ok(c) => c, Err(e) => return e };
    let name = path.into_inner();
    match conn.execute("DELETE FROM tags WHERE name = ?1", params![name]) {
        Ok(0) => HttpResponse::NotFound().json(ApiResponse::<()>::err("标签不存在")),
        Ok(_) => HttpResponse::Ok().json(ApiResponse::ok(true)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("删除标签失败: {}", e))),
    }
}
