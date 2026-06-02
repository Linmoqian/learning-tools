use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Task {
    pub id: Option<i64>,
    pub name: String,
    pub category: String,
    pub task_type: String,
    pub description: Option<String>,
    pub estimated_time: i64,
    pub preferred_time: Option<String>,
    pub deadline: Option<String>,
    pub resistance: String,
    pub energy_required: String,
    pub rarity: String,
    pub priority: i64,
    pub success_rate: f64,
    pub refusal_count: i64,
    pub is_daily: bool,
    pub repeat_type: String,
    pub task_profile: String,
    pub completed: bool,
    pub in_discard_pile: bool,
    pub completed_count: i64,
    pub draw_count_today: i64,
    pub min_push_time: String,
    pub last_drawn_at: Option<String>,
    pub last_completed_at: Option<String>,
    pub next_available_at: Option<String>,
    pub prerequisite_ids: Vec<i64>,
    pub is_unlocked: bool,
    pub parent_task_id: Option<i64>,
    pub group_id: Option<String>,
    pub difficulty: Option<i64>,
    pub tags: Vec<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateTaskRequest {
    pub name: String,
    pub category: Option<String>,
    pub description: Option<String>,
    pub estimated_time: Option<i64>,
    pub preferred_time: Option<String>,
    pub deadline: Option<String>,
    pub resistance: Option<String>,
    pub energy_required: Option<String>,
    pub priority: Option<i64>,
    pub repeat_type: Option<String>,
    pub task_profile: Option<String>,
    pub tags: Option<Vec<String>>,
    pub prerequisite_ids: Option<Vec<i64>>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateTaskRequest {
    pub name: Option<String>,
    pub category: Option<String>,
    pub description: Option<String>,
    pub estimated_time: Option<i64>,
    pub preferred_time: Option<String>,
    pub deadline: Option<String>,
    pub resistance: Option<String>,
    pub energy_required: Option<String>,
    pub priority: Option<i64>,
    pub repeat_type: Option<String>,
    pub task_profile: Option<String>,
    pub completed: Option<bool>,
    pub in_discard_pile: Option<bool>,
    pub tags: Option<Vec<String>>,
    pub prerequisite_ids: Option<Vec<i64>>,
    pub is_unlocked: Option<bool>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CompleteTaskRequest {
    pub feedback: Option<TaskFeedbackInput>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct TaskFeedbackInput {
    pub energy_after: i64,
    pub mood_after: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DetectCycleRequest {
    pub task_id: i64,
    pub proposed_prerequisite_ids: Vec<i64>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DetectCycleResponse {
    pub has_cycle: bool,
    pub cycle_description: String,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ChainUnlockResponse {
    pub unlocked_task_names: Vec<String>,
    pub unlocked_task_ids: Vec<i64>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ApiResponse<T: Serialize> {
    pub success: bool,
    pub data: Option<T>,
    pub error: Option<String>,
}

impl<T: Serialize> ApiResponse<T> {
    pub fn ok(data: T) -> Self {
        ApiResponse { success: true, data: Some(data), error: None }
    }
    pub fn err(msg: impl Into<String>) -> Self {
        ApiResponse { success: false, data: None, error: Some(msg.into()) }
    }
}

impl Task {
    pub fn from_row(
        row: &rusqlite::Row,
        tags: Vec<String>,
    ) -> Result<Self, rusqlite::Error> {
        let prereq_str: String = row.get("prerequisite_ids")?;
        let prereq_ids: Vec<i64> = serde_json::from_str(&prereq_str).unwrap_or_default();

        Ok(Task {
            id: Some(row.get("id")?),
            name: row.get("name")?,
            category: row.get("category")?,
            task_type: row.get("task_type")?,
            description: row.get("description")?,
            estimated_time: row.get("estimated_time")?,
            preferred_time: row.get("preferred_time")?,
            deadline: row.get("deadline")?,
            resistance: row.get("resistance")?,
            energy_required: row.get("energy_required")?,
            rarity: row.get("rarity")?,
            priority: row.get("priority")?,
            success_rate: row.get("success_rate")?,
            refusal_count: row.get("refusal_count")?,
            is_daily: row.get::<_, i64>("is_daily")? != 0,
            repeat_type: row.get("repeat_type")?,
            task_profile: row.get("task_profile")?,
            completed: row.get::<_, i64>("completed")? != 0,
            in_discard_pile: row.get::<_, i64>("in_discard_pile")? != 0,
            completed_count: row.get("completed_count")?,
            draw_count_today: row.get("draw_count_today")?,
            min_push_time: row.get("min_push_time")?,
            last_drawn_at: row.get("last_drawn_at")?,
            last_completed_at: row.get("last_completed_at")?,
            next_available_at: row.get("next_available_at")?,
            prerequisite_ids: prereq_ids,
            is_unlocked: row.get::<_, i64>("is_unlocked")? != 0,
            parent_task_id: row.get("parent_task_id")?,
            group_id: row.get("group_id")?,
            difficulty: row.get("difficulty")?,
            tags,
            created_at: row.get("created_at")?,
            updated_at: row.get("updated_at")?,
        })
    }

    pub fn now_iso() -> String {
        Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string()
    }

    pub fn default_with_name(name: String) -> Self {
        let now = Self::now_iso();
        Task {
            id: None,
            name,
            category: "daily".into(),
            task_type: "normal".into(),
            description: None,
            estimated_time: 25,
            preferred_time: None,
            deadline: None,
            resistance: "medium".into(),
            energy_required: "medium".into(),
            rarity: "common".into(),
            priority: 5,
            success_rate: 0.0,
            refusal_count: 0,
            is_daily: false,
            repeat_type: "none".into(),
            task_profile: "deadline_flexible".into(),
            completed: false,
            in_discard_pile: false,
            completed_count: 0,
            draw_count_today: 0,
            min_push_time: "20:00".into(),
            last_drawn_at: None,
            last_completed_at: None,
            next_available_at: None,
            prerequisite_ids: vec![],
            is_unlocked: true,
            parent_task_id: None,
            group_id: None,
            difficulty: None,
            tags: vec![],
            created_at: now.clone(),
            updated_at: now,
        }
    }
}
