use actix_web::{web, HttpResponse, get, post, put, delete};
use rusqlite::params;
use serde_json;
use std::path::PathBuf;

use crate::db;
use crate::models::task::ApiResponse;
use crate::models::knowledge::*;
use crate::services::knowledge_service;

// ===== 获取笔记目录路径 =====
fn notes_dir(state: &web::Data<crate::AppState>) -> PathBuf {
    state.notes_dir.clone()
}

fn db_conn(state: &web::Data<crate::AppState>) -> Result<std::sync::MutexGuard<'_, rusqlite::Connection>, HttpResponse> {
    state.db.lock().map_err(|_| HttpResponse::InternalServerError().json(ApiResponse::<()>::err("数据库锁获取失败")))
}

// ===== 从 SQLite 加载知识点 =====
fn load_kps(conn: &rusqlite::Connection) -> Vec<KnowledgePoint> {
    let mut stmt = match conn.prepare("SELECT id, name, subject, description, related_points FROM knowledge_points ORDER BY name") {
        Ok(s) => s,
        Err(_) => return vec![],
    };

    stmt.query_map([], |row| {
        let rp_str: String = row.get("related_points")?;
        let related: Vec<String> = serde_json::from_str(&rp_str).unwrap_or_default();
        Ok(KnowledgePoint {
            id: Some(row.get("id")?),
            name: row.get("name")?,
            subject: row.get("subject")?,
            description: row.get("description")?,
            linked_from: vec![],
            related_points: related,
        })
    })
    .unwrap()
    .filter_map(|r| r.ok())
    .collect()
}

// ===== GET /api/knowledge/notes =====
#[get("/api/knowledge/notes")]
pub async fn list_notes(state: web::Data<crate::AppState>) -> HttpResponse {
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    HttpResponse::Ok().json(ApiResponse::ok(notes))
}

// ===== GET /api/knowledge/notes/{name} =====
#[get("/api/knowledge/notes/{name}")]
pub async fn get_note(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let name = path.into_inner();
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    match notes.into_iter().find(|n| n.name == name) {
        Some(note) => HttpResponse::Ok().json(ApiResponse::ok(note)),
        None => HttpResponse::NotFound().json(ApiResponse::<()>::err("笔记不存在")),
    }
}

// ===== POST /api/knowledge/notes =====
#[post("/api/knowledge/notes")]
pub async fn create_note(
    state: web::Data<crate::AppState>,
    body: web::Json<CreateNoteRequest>,
) -> HttpResponse {
    let nd = notes_dir(&state);
    let now = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();

    let note = Note {
        id: String::new(), // will be set by write_note_file
        name: body.name.clone(),
        title: body.title.clone(),
        subject: body.subject.clone(),
        tags: body.tags.clone().unwrap_or_default(),
        wiki_links: body.wiki_links.clone().unwrap_or_default(),
        content: body.content.clone(),
        images: body.images.clone().unwrap_or_default(),
        created_at: now.clone(),
        updated_at: now,
    };

    match knowledge_service::write_note_file(&nd, &note) {
        Ok(_) => {
            // Re-scan to get the full note with id
            let notes = knowledge_service::scan_notes_dir(&nd);
            match notes.into_iter().find(|n| n.name == body.name) {
                Some(n) => HttpResponse::Ok().json(ApiResponse::ok(n)),
                None => HttpResponse::Ok().json(ApiResponse::ok(note)),
            }
        }
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(e)),
    }
}

// ===== PUT /api/knowledge/notes/{name} =====
#[put("/api/knowledge/notes/{name}")]
pub async fn update_note(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
    body: web::Json<UpdateNoteRequest>,
) -> HttpResponse {
    let nd = notes_dir(&state);
    let name = path.into_inner();
    let notes = knowledge_service::scan_notes_dir(&nd);
    let mut existing = match notes.into_iter().find(|n| n.name == name) {
        Some(n) => n,
        None => return HttpResponse::NotFound().json(ApiResponse::<()>::err("笔记不存在")),
    };

    if let Some(ref v) = body.title { existing.title = v.clone(); }
    if let Some(ref v) = body.subject { existing.subject = v.clone(); }
    if let Some(ref v) = body.content { existing.content = v.clone(); }
    if let Some(ref v) = body.tags { existing.tags = v.clone(); }
    if let Some(ref v) = body.wiki_links { existing.wiki_links = v.clone(); }
    if let Some(ref v) = body.images { existing.images = v.clone(); }
    existing.updated_at = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();

    match knowledge_service::write_note_file(&nd, &existing) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::ok(existing)),
        Err(e) => HttpResponse::InternalServerError().json(ApiResponse::<()>::err(e)),
    }
}

// ===== DELETE /api/knowledge/notes/{name} =====
#[delete("/api/knowledge/notes/{name}")]
pub async fn delete_note(
    state: web::Data<crate::AppState>,
    path: web::Path<String>,
) -> HttpResponse {
    let nd = notes_dir(&state);
    let name = path.into_inner();
    match knowledge_service::delete_note_file(&nd, &name) {
        Ok(_) => HttpResponse::Ok().json(ApiResponse::ok(true)),
        Err(e) => HttpResponse::NotFound().json(ApiResponse::<()>::err(e)),
    }
}

// ===== GET /api/knowledge/points =====
#[get("/api/knowledge/points")]
pub async fn list_knowledge_points(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };

    // 先加载 KPs，再计算 linkedFrom
    let mut kps = load_kps(&conn);
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));

    // 为每个 KP 计算被哪些笔记引用
    let kp_name_set: std::collections::HashSet<String> =
        kps.iter().map(|kp| kp.name.clone()).collect();
    let mut linked: std::collections::HashMap<String, Vec<String>> = std::collections::HashMap::new();

    for note in &notes {
        for link in &note.wiki_links {
            if kp_name_set.contains(link) {
                linked.entry(link.clone()).or_default().push(note.id.clone());
            }
        }
    }

    for kp in &mut kps {
        kp.linked_from = linked.remove(&kp.name).unwrap_or_default();
    }

    HttpResponse::Ok().json(ApiResponse::ok(kps))
}

// ===== POST /api/knowledge/points =====
#[post("/api/knowledge/points")]
pub async fn create_knowledge_point(
    state: web::Data<crate::AppState>,
    body: web::Json<CreateKnowledgePointRequest>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let rp_json = serde_json::to_string(&body.related_points.clone().unwrap_or_default()).unwrap_or_else(|_| "[]".into());

    match conn.execute(
        "INSERT INTO knowledge_points (name, subject, description, related_points) VALUES (?1, ?2, ?3, ?4)",
        params![body.name, body.subject, body.description, rp_json],
    ) {
        Ok(_) => {
            let id = conn.last_insert_rowid();
            // Re-load and return with linkedFrom
            let mut kps = load_kps(&conn);
            kps.retain(|kp| kp.id == Some(id));
            let kp = kps.into_iter().next()
                .unwrap_or(KnowledgePoint {
                    id: Some(id),
                    name: body.name.clone(),
                    subject: body.subject.clone(),
                    description: body.description.clone(),
                    linked_from: vec![],
                    related_points: body.related_points.clone().unwrap_or_default(),
                });
            HttpResponse::Ok().json(ApiResponse::ok(kp))
        }
        Err(e) => {
            if e.to_string().contains("UNIQUE") {
                HttpResponse::BadRequest().json(ApiResponse::<()>::err("知识点已存在"))
            } else {
                HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("创建失败: {}", e)))
            }
        }
    }
}

// ===== GET /api/knowledge/points/{id} =====
#[get("/api/knowledge/points/{id}")]
pub async fn get_knowledge_point(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let kp_id = path.into_inner();

    let kps = load_kps(&conn);
    match kps.into_iter().find(|kp| kp.id == Some(kp_id)) {
        Some(kp) => HttpResponse::Ok().json(ApiResponse::ok(kp)),
        None => HttpResponse::NotFound().json(ApiResponse::<()>::err("知识点不存在")),
    }
}

// ===== PUT /api/knowledge/points/{id} =====
#[put("/api/knowledge/points/{id}")]
pub async fn update_knowledge_point(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
    body: web::Json<CreateKnowledgePointRequest>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let kp_id = path.into_inner();
    let rp_json = serde_json::to_string(&body.related_points.clone().unwrap_or_default()).unwrap_or_else(|_| "[]".into());

    conn.execute(
        "UPDATE knowledge_points SET name = ?1, subject = ?2, description = ?3, related_points = ?4 WHERE id = ?5",
        params![body.name, body.subject, body.description, rp_json, kp_id],
    ).map(|affected| {
        if affected == 0 {
            HttpResponse::NotFound().json(ApiResponse::<()>::err("知识点不存在"))
        } else {
            HttpResponse::Ok().json(ApiResponse::ok(true))
        }
    }).unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("更新失败: {}", e))))
}

// ===== DELETE /api/knowledge/points/{id} =====
#[delete("/api/knowledge/points/{id}")]
pub async fn delete_knowledge_point(
    state: web::Data<crate::AppState>,
    path: web::Path<i64>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let kp_id = path.into_inner();

    conn.execute("DELETE FROM knowledge_points WHERE id = ?1", params![kp_id])
        .map(|affected| {
            if affected == 0 {
                HttpResponse::NotFound().json(ApiResponse::<()>::err("知识点不存在"))
            } else {
                HttpResponse::Ok().json(ApiResponse::ok(true))
            }
        })
        .unwrap_or_else(|e| HttpResponse::InternalServerError().json(ApiResponse::<()>::err(format!("删除失败: {}", e))))
}

// ===== GET /api/knowledge/analysis =====
#[get("/api/knowledge/analysis")]
pub async fn analysis(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    let kps = load_kps(&conn);

    let result = knowledge_service::analyze_links(&notes, &kps);
    HttpResponse::Ok().json(ApiResponse::ok(result))
}

// ===== GET /api/knowledge/graph =====
#[get("/api/knowledge/graph")]
pub async fn graph(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    let kps = load_kps(&conn);

    let data = knowledge_service::build_graph(&notes, &kps);
    HttpResponse::Ok().json(ApiResponse::ok(data))
}

// ===== GET /api/knowledge/subjects =====
#[get("/api/knowledge/subjects")]
pub async fn subject_stats(state: web::Data<crate::AppState>) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    let kps = load_kps(&conn);

    let link_result = knowledge_service::analyze_links(&notes, &kps);
    let stats = knowledge_service::get_subject_stats(&link_result);
    HttpResponse::Ok().json(ApiResponse::ok(stats))
}

// ===== POST /api/knowledge/search =====
#[post("/api/knowledge/search")]
pub async fn search(
    state: web::Data<crate::AppState>,
    body: web::Json<SearchRequest>,
) -> HttpResponse {
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let notes = knowledge_service::scan_notes_dir(&notes_dir(&state));
    let kps = load_kps(&conn);

    let results = knowledge_service::search_items(
        &notes,
        &kps,
        &body.query,
        body.subject_filter.as_deref(),
    );
    HttpResponse::Ok().json(ApiResponse::ok(results))
}

// ===== POST /api/knowledge/init-examples =====
#[post("/api/knowledge/init-examples")]
pub async fn init_examples(state: web::Data<crate::AppState>) -> HttpResponse {
    let nd = notes_dir(&state);
    let conn = match db_conn(&state) { Ok(c) => c, Err(e) => return e };
    let now = chrono::Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();

    // 如果已经有笔记，跳过
    let existing = knowledge_service::scan_notes_dir(&nd);
    if !existing.is_empty() {
        return HttpResponse::Ok().json(ApiResponse::ok(false));
    }

    // 写入示例笔记
    let examples = vec![
        ("函数的概念与基本要素", "高数", "函数是数学中最重要的基本概念之一。本章从函数的定义出发，介绍定义域、值域、对应法则三要素。\n\n相关知识点：[[数列的极限]]"),
        ("数列的极限", "高数", "极限是高等数学的基石。数列极限的定义使用ε-N语言精确描述。\n\n相关知识点：[[函数的极限与运算法则]]、[[无穷小与无穷大]]"),
        ("求导法则与基本公式", "高数", "导数是函数变化率的度量。本章系统介绍基本求导公式和运算法则。\n\n相关知识点：[[函数的连续性与间断点]]"),
        ("矩阵的运算", "线代", "矩阵是线性代数的核心研究对象。介绍矩阵的基本运算和性质。\n\n相关知识点：[[矩阵的秩]]、[[行列式的定义与性质]]"),
        ("行列式的定义与性质", "线代", "行列式是线性代数中的重要工具。\n\n相关知识点：[[克莱姆法则]]、[[矩阵的运算]]"),
        ("质点运动描述的物理量", "大物", "力学是物理学的基础。描述质点运动需要位置矢量、位移、速度、加速度等概念。\n\n相关知识点：[[自然坐标系与加速度分解]]"),
    ];

    for (title, subject, content) in &examples {
        let note = Note {
            id: String::new(),
            name: title.to_string(),
            title: title.to_string(),
            subject: subject.to_string(),
            tags: vec![],
            wiki_links: vec![],
            content: content.to_string(),
            images: vec![],
            created_at: now.clone(),
            updated_at: now.clone(),
        };
        let _ = knowledge_service::write_note_file(&nd, &note);
    }

    // 写入示例知识点
    let kp_examples = vec![
        ("数列的极限", "高数", "数列极限的定义、性质与收敛判别"),
        ("函数的极限与运算法则", "高数", "极限的四则运算、复合函数极限"),
        ("无穷小与无穷大", "高数", "无穷小的阶、等价无穷小替换"),
        ("函数的连续性与间断点", "高数", "连续定义、间断点分类"),
        ("矩阵的秩", "线代", "秩的定义、行阶梯形、秩的计算"),
        ("行列式的定义与性质", "线代", "行列式的展开、性质、计算方法"),
        ("克莱姆法则", "线代", "用行列式计算线性方程组"),
        ("自然坐标系与加速度分解", "大物", "切向加速度、法向加速度"),
    ];

    for (name, subject, desc) in &kp_examples {
        let _ = conn.execute(
            "INSERT OR IGNORE INTO knowledge_points (name, subject, description) VALUES (?1, ?2, ?3)",
            params![name, subject, desc],
        );
    }

    HttpResponse::Ok().json(ApiResponse::ok(true))
}
