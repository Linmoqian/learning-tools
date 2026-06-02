use crate::models::task::Task;
use chrono::{DateTime, Utc};
use rand::Rng;
use serde_json;
use std::collections::HashMap;

/// 加权随机选 top-n 任务（匹配 frontend algorithms.ts + Python task_service.py）
pub fn get_top_weighted(tasks: &[Task], n: usize, current_energy: &str) -> Vec<Task> {
    if tasks.is_empty() {
        return vec![];
    }
    let mut weighted: Vec<(f64, &Task)> = tasks
        .iter()
        .map(|t| (calculate_full_weight(t, current_energy), t))
        .collect();
    weighted.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

    weighted.into_iter().take(n).map(|(_, t)| t.clone()).collect()
}

/// 加权随机选一个任务
pub fn select_weighted_random(tasks: &[Task], current_energy: &str) -> Option<Task> {
    if tasks.is_empty() {
        return None;
    }
    let weights: Vec<f64> = tasks.iter().map(|t| calculate_full_weight(t, current_energy)).collect();
    let total: f64 = weights.iter().sum();
    if total <= 0.0 {
        let mut rng = rand::thread_rng();
        return Some(tasks[rng.gen_range(0..tasks.len())].clone());
    }
    let mut rng = rand::thread_rng();
    let mut r = rng.gen::<f64>() * total;
    for (i, w) in weights.iter().enumerate() {
        r -= w;
        if r <= 0.0 {
            return Some(tasks[i].clone());
        }
    }
    Some(tasks[tasks.len() - 1].clone())
}

/// 完整权重计算（与前端 algorithms.ts 精确一致）
pub fn calculate_full_weight(task: &Task, current_energy: &str) -> f64 {
    let mut w = 1.0;
    w *= priority_weight(task);
    w *= deadline_urgency(task);
    w *= energy_match(task, current_energy);
    w *= resistance_factor(task);
    w *= success_rate_factor(task);
    w *= refusal_penalty(task);
    w *= profile_strategy_weight(task);
    w *= cooldown_factor(task);
    w.max(0.01)
}

fn priority_weight(task: &Task) -> f64 {
    task.priority as f64 / 5.0
}

fn deadline_urgency(task: &Task) -> f64 {
    match &task.deadline {
        None => 1.0,
        Some(d) => {
            let now = Utc::now();
            let deadline = match d.parse::<DateTime<Utc>>() {
                Ok(dt) => dt,
                Err(_) => return 1.0,
            };
            if deadline <= now {
                return 3.0;
            }
            let days_left = (deadline - now).num_hours() as f64 / 24.0;
            if days_left <= 1.0 { 2.5 }
            else if days_left <= 3.0 { 1.5 }
            else if days_left <= 7.0 { 1.0 + (7.0 - days_left) * 0.1 }
            else { 0.5 }
        }
    }
}

fn energy_match(task: &Task, current_energy: &str) -> f64 {
    let score: HashMap<&str, f64> = [("low", 0.0), ("medium", 1.0), ("high", 2.0)].iter().cloned().collect();
    let t = score.get(task.energy_required.as_str()).unwrap_or(&1.0);
    let c = score.get(current_energy).unwrap_or(&1.0);
    (1.5 - (t - c).abs() * 0.3).max(0.5)
}

fn resistance_factor(task: &Task) -> f64 {
    match task.resistance.as_str() {
        "low" => 1.0,
        "medium" => 0.8,
        "high" => 0.6,
        _ => 1.0,
    }
}

fn success_rate_factor(task: &Task) -> f64 {
    0.5 + task.success_rate * 0.5
}

fn refusal_penalty(task: &Task) -> f64 {
    (1.0 - task.refusal_count as f64 * 0.1).max(0.3)
}

fn profile_strategy_weight(task: &Task) -> f64 {
    let now = Utc::now();
    match task.task_profile.as_str() {
        "daily_habit" => 0.0,
        "weekly_routine" => {
            let weekday = now.format("%u").to_string().parse::<u32>().unwrap_or(7);
            match weekday {
                1..=4 => 0.3,  // Mon-Thu
                5..=6 => 1.5,  // Fri-Sat
                _ => 3.0,      // Sun
            }
        }
        "deadline_flexible" => {
            match &task.deadline {
                None => 1.0,
                Some(d) => {
                    let deadline = match d.parse::<DateTime<Utc>>() {
                        Ok(dt) => dt,
                        Err(_) => return 1.0,
                    };
                    let days = (deadline - now).num_hours() as f64 / 24.0;
                    if days > 7.0 { 0.5 }
                    else if days > 3.0 { 1.0 }
                    else if days > 1.0 { 1.5 }
                    else { 2.5 }
                }
            }
        }
        "deadline_progressive" => 1.0,
        _ => 1.0,
    }
}

fn cooldown_factor(task: &Task) -> f64 {
    if task.draw_count_today >= 3 {
        0.2
    } else {
        1.0
    }
}

/// 链式解锁：完成任务后递归解锁依赖任务
pub fn chain_unlock(
    conn: &rusqlite::Connection,
    task_id: i64,
) -> Result<(Vec<String>, Vec<i64>), rusqlite::Error> {
    use rusqlite::params;
    let mut unlocked_names = Vec::new();
    let mut unlocked_ids = Vec::new();

    let dependents: Vec<(i64, String)> = {
        let mut stmt = conn.prepare(
            "SELECT id, name FROM tasks WHERE is_unlocked = 0 AND prerequisite_ids != '[]' AND prerequisite_ids IS NOT NULL"
        )?;
        let rows = stmt.query_map([], |row| {
            let id: i64 = row.get(0)?;
            let name: String = row.get(1)?;
            Ok((id, name))
        })?;
        let mut deps = Vec::new();
        for r in rows {
            let (id, name) = r?;
            if task_is_dependent(conn, id, task_id)? {
                deps.push((id, name));
            }
        }
        deps
    };

    for (dep_id, dep_name) in dependents {
        if check_all_prereqs_done(conn, dep_id)? {
            conn.execute("UPDATE tasks SET is_unlocked = 1, updated_at = ?1 WHERE id = ?2",
                params![Task::now_iso(), dep_id])?;
            unlocked_names.push(dep_name);
            unlocked_ids.push(dep_id);
            let (nested_names, nested_ids) = chain_unlock(conn, dep_id)?;
            unlocked_names.extend(nested_names);
            unlocked_ids.extend(nested_ids);
        }
    }

    Ok((unlocked_names, unlocked_ids))
}

fn task_is_dependent(conn: &rusqlite::Connection, task_id: i64, depends_on_id: i64) -> Result<bool, rusqlite::Error> {
    let prereq_str: String = conn.query_row(
        "SELECT prerequisite_ids FROM tasks WHERE id = ?1",
        rusqlite::params![task_id],
        |row| row.get(0),
    ).unwrap_or_else(|_| "[]".into());

    let prereq_ids: Vec<i64> = serde_json::from_str(&prereq_str).unwrap_or_default();
    Ok(prereq_ids.contains(&depends_on_id))
}

fn check_all_prereqs_done(conn: &rusqlite::Connection, task_id: i64) -> Result<bool, rusqlite::Error> {
    let prereq_str: String = conn.query_row(
        "SELECT prerequisite_ids FROM tasks WHERE id = ?1",
        rusqlite::params![task_id],
        |row| row.get(0),
    ).unwrap_or_else(|_| "[]".into());

    let prereq_ids: Vec<i64> = serde_json::from_str(&prereq_str).unwrap_or_default();
    if prereq_ids.is_empty() {
        return Ok(true);
    }
    for pid in &prereq_ids {
        let done: bool = conn.query_row(
            "SELECT completed FROM tasks WHERE id = ?1",
            rusqlite::params![pid],
            |row| row.get::<_, i64>(0).map(|v| v != 0),
        ).unwrap_or(false);
        if !done {
            return Ok(false);
        }
    }
    Ok(true)
}

/// 循环依赖检测（DFS）
pub fn detect_cycle(
    conn: &rusqlite::Connection,
    task_id: i64,
    proposed_ids: &[i64],
) -> Result<bool, rusqlite::Error> {
    if proposed_ids.is_empty() {
        return Ok(false);
    }
    let mut visited = std::collections::HashSet::new();

    fn dfs(conn: &rusqlite::Connection, current: i64, target: i64, visited: &mut std::collections::HashSet<i64>) -> Result<bool, rusqlite::Error> {
        if current == target {
            return Ok(true);
        }
        if !visited.insert(current) {
            return Ok(false);
        }
        let prereq_str: String = match conn.query_row(
            "SELECT prerequisite_ids FROM tasks WHERE id = ?1",
            rusqlite::params![current],
            |row| row.get(0),
        ) {
            Ok(s) => s,
            Err(_) => return Ok(false),
        };
        let prereq_ids: Vec<i64> = serde_json::from_str(&prereq_str).unwrap_or_default();
        for pid in &prereq_ids {
            if dfs(conn, *pid, target, visited)? {
                return Ok(true);
            }
        }
        Ok(false)
    }

    for pid in proposed_ids {
        if dfs(conn, *pid, task_id, &mut visited)? {
            return Ok(true);
        }
    }
    Ok(false)
}
