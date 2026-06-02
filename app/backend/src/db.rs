use rusqlite::{Connection, params};
use std::path::Path;

pub fn init_db(db_path: &str) -> Result<Connection, rusqlite::Error> {
    let exists = Path::new(db_path).exists();
    let conn = Connection::open(db_path)?;

    if !exists {
        conn.execute_batch("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")?;
    } else {
        conn.execute_batch("PRAGMA foreign_keys=ON;")?;
    }

    create_tables(&conn)?;
    let _ = ensure_defaults(&conn);
    Ok(conn)
}

fn create_tables(conn: &Connection) -> Result<(), rusqlite::Error> {
    conn.execute_batch("
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            category        TEXT NOT NULL DEFAULT 'daily',
            task_type       TEXT NOT NULL DEFAULT 'normal',
            description     TEXT,
            estimated_time  INTEGER NOT NULL DEFAULT 30,
            preferred_time  TEXT,
            deadline        TEXT,
            resistance      TEXT NOT NULL DEFAULT 'medium',
            energy_required TEXT NOT NULL DEFAULT 'medium',
            rarity          TEXT NOT NULL DEFAULT 'common',
            priority        INTEGER NOT NULL DEFAULT 5,
            success_rate    REAL NOT NULL DEFAULT 0.0,
            refusal_count   INTEGER NOT NULL DEFAULT 0,
            is_daily        INTEGER NOT NULL DEFAULT 0,
            repeat_type     TEXT NOT NULL DEFAULT 'none',
            task_profile    TEXT NOT NULL DEFAULT 'deadline_flexible',
            completed       INTEGER NOT NULL DEFAULT 0,
            in_discard_pile INTEGER NOT NULL DEFAULT 0,
            completed_count INTEGER NOT NULL DEFAULT 0,
            draw_count_today INTEGER NOT NULL DEFAULT 0,
            min_push_time   TEXT NOT NULL DEFAULT '20:00',
            last_drawn_at   TEXT,
            last_completed_at TEXT,
            next_available_at TEXT,
            prerequisite_ids TEXT NOT NULL DEFAULT '[]',
            is_unlocked     INTEGER NOT NULL DEFAULT 1,
            parent_task_id  INTEGER,
            group_id        TEXT,
            difficulty      INTEGER,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER NOT NULL,
            tag_id  INTEGER NOT NULL,
            PRIMARY KEY (task_id, tag_id),
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id)  REFERENCES tags(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS daily_user_state (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            date              TEXT NOT NULL UNIQUE,
            daily_tone        TEXT NOT NULL DEFAULT 'normal',
            energy_morning    INTEGER,
            energy_afternoon  INTEGER,
            energy_evening    INTEGER,
            bed_time          TEXT,
            sleep_early_streak INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS gacha_records (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp      TEXT NOT NULL,
            pool_name      TEXT NOT NULL,
            available_time INTEGER NOT NULL,
            task_id        INTEGER,
            accepted       INTEGER NOT NULL DEFAULT 1,
            refusal_reason TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS task_rejection_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id   INTEGER NOT NULL,
            reason    TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS task_completion_feedback (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id      INTEGER NOT NULL,
            energy_after INTEGER,
            mood_after   INTEGER,
            timestamp    TEXT NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS user_schedule (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL,
            time_slot  TEXT NOT NULL,
            activity   TEXT NOT NULL,
            notes      TEXT DEFAULT '',
            is_regular INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS daily_schedules (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            date      TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            activity  TEXT NOT NULL,
            notes     TEXT DEFAULT '',
            UNIQUE(date, time_slot)
        );

        CREATE TABLE IF NOT EXISTS activities (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS settings (
            id    INTEGER PRIMARY KEY CHECK (id = 1),
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS _meta (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    ")?;
    Ok(())
}

fn ensure_defaults(conn: &Connection) -> Result<(), rusqlite::Error> {
    // Default activities
    let defaults = ["无安排", "学习", "工作", "阅读", "运动", "休息"];
    for a in &defaults {
        conn.execute("INSERT OR IGNORE INTO activities (name) VALUES (?1)", params![a])?;
    }

    // Default settings
    conn.execute(
        "INSERT OR IGNORE INTO settings (id, value) VALUES (1, ?1)",
        params![r##"{"llm":{"apiUrl":"","apiKey":"","modelName":"gpt-4o"},"mineru":{"apiUrl":"","apiKey":""},"theme":{"primaryColor":"#f5e6a0","primaryColorLight":"#fdf6d4","primaryColorDark":"#d4c06a","themeMode":"light"}}"##],
    )?;

    Ok(())
}

pub fn get_task_tags(conn: &Connection, task_id: i64) -> Result<Vec<String>, rusqlite::Error> {
    let mut stmt = conn.prepare(
        "SELECT t.name FROM tags t JOIN task_tags tt ON t.id = tt.tag_id WHERE tt.task_id = ?1"
    )?;
    let rows = stmt.query_map(params![task_id], |row| row.get::<_, String>(0))?;
    let mut tags = Vec::new();
    for r in rows {
        tags.push(r?);
    }
    Ok(tags)
}

pub fn set_task_tags(conn: &Connection, task_id: i64, tag_names: &[String]) -> Result<(), rusqlite::Error> {
    conn.execute("DELETE FROM task_tags WHERE task_id = ?1", params![task_id])?;
    for name in tag_names {
        let name = name.trim();
        if name.is_empty() { continue; }
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?1)", params![name])?;
        if let Ok(tag_id) = conn.query_row(
            "SELECT id FROM tags WHERE name = ?1", params![name], |row| row.get::<_, i64>(0)
        ) {
            conn.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?1, ?2)",
                params![task_id, tag_id],
            )?;
        }
    }
    Ok(())
}
