mod db;
mod models;
mod services;
mod routes;

use actix_web::{web, App, HttpServer, middleware};
use actix_cors::Cors;
use std::path::PathBuf;
use std::sync::Mutex;

pub struct AppState {
    pub db: Mutex<rusqlite::Connection>,
    pub notes_dir: PathBuf,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info")).init();

    let host = std::env::var("HOST").unwrap_or_else(|_| "127.0.0.1".into());
    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "8900".into())
        .parse()
        .unwrap_or(8900);
    let db_path = std::env::var("DB_PATH").unwrap_or_else(|_| "data/learning_tools.db".into());
    let notes_dir = std::env::var("NOTES_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            let mut p = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));
            p.push("data");
            p.push("notes");
            p
        });

    // Ensure directories exist
    if let Some(parent) = std::path::Path::new(&db_path).parent() {
        std::fs::create_dir_all(parent).ok();
    }
    std::fs::create_dir_all(&notes_dir).ok();

    let connection = db::init_db(&db_path).expect("数据库初始化失败");

    log::info!("学习工具后端启动 → http://{}:{}", host, port);
    log::info!("数据库: {}", db_path);
    log::info!("笔记目录: {:?}", notes_dir);

    // Count existing notes
    let note_count = std::fs::read_dir(&notes_dir)
        .map(|entries| entries.filter_map(|e| e.ok())
            .filter(|e| e.path().extension().and_then(|s| s.to_str()) == Some("md"))
            .count())
        .unwrap_or(0);
    log::info!("笔记数量: {}", note_count);

    let data = web::Data::new(AppState {
        db: Mutex::new(connection),
        notes_dir,
    });

    HttpServer::new(move || {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);

        App::new()
            .app_data(data.clone())
            .wrap(cors)
            .wrap(middleware::Logger::default())

            // Tasks
            .service(routes::task_routes::list_tasks)
            .service(routes::task_routes::create_task)
            .service(routes::task_routes::get_task)
            .service(routes::task_routes::update_task)
            .service(routes::task_routes::delete_task)
            .service(routes::task_routes::complete_task)
            .service(routes::task_routes::skip_task)
            .service(routes::task_routes::record_draw)
            .service(routes::task_routes::discard_task)
            .service(routes::task_routes::restore_task)
            .service(routes::task_routes::reset_discard)
            .service(routes::task_routes::reset_periodic)
            .service(routes::task_routes::detect_cycle)

            // Tags
            .service(routes::task_routes::list_tags)
            .service(routes::task_routes::create_tag)
            .service(routes::task_routes::delete_tag)

            // Gacha
            .service(routes::gacha_routes::draw)
            .service(routes::gacha_routes::plan_draw)
            .service(routes::gacha_routes::accept_draw)
            .service(routes::gacha_routes::reject_draw)
            .service(routes::gacha_routes::list_records)
            .service(routes::gacha_routes::list_rejections)

            // Schedule
            .service(routes::schedule_routes::get_slots)
            .service(routes::schedule_routes::get_day_schedule)
            .service(routes::schedule_routes::set_schedule)
            .service(routes::schedule_routes::delete_schedule)
            .service(routes::schedule_routes::get_weekly)

            // Activities
            .service(routes::schedule_routes::list_activities)
            .service(routes::schedule_routes::create_activity)
            .service(routes::schedule_routes::delete_activity)

            // Daily State
            .service(routes::state_routes::get_daily_state)
            .service(routes::state_routes::set_daily_state)
            .service(routes::state_routes::record_sleep)

            // Settings
            .service(routes::settings_routes::get_settings)
            .service(routes::settings_routes::update_settings)
            .service(routes::settings_routes::reset_settings)

            // Knowledge
            .service(routes::knowledge_routes::list_notes)
            .service(routes::knowledge_routes::get_note)
            .service(routes::knowledge_routes::create_note)
            .service(routes::knowledge_routes::update_note)
            .service(routes::knowledge_routes::delete_note)
            .service(routes::knowledge_routes::list_knowledge_points)
            .service(routes::knowledge_routes::create_knowledge_point)
            .service(routes::knowledge_routes::get_knowledge_point)
            .service(routes::knowledge_routes::update_knowledge_point)
            .service(routes::knowledge_routes::delete_knowledge_point)
            .service(routes::knowledge_routes::analysis)
            .service(routes::knowledge_routes::graph)
            .service(routes::knowledge_routes::subject_stats)
            .service(routes::knowledge_routes::search)
            .service(routes::knowledge_routes::init_examples)
    })
    .bind(format!("{}:{}", host, port))?
    .run()
    .await
}
