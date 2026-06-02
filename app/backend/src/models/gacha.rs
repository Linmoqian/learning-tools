use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct GachaRecord {
    pub id: Option<i64>,
    pub timestamp: String,
    pub pool_name: String,
    pub available_time: i64,
    pub task_id: Option<i64>,
    pub accepted: bool,
    pub refusal_reason: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TaskRejectionLog {
    pub id: Option<i64>,
    pub task_id: i64,
    pub reason: String,
    pub timestamp: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct TaskCompletionFeedback {
    pub id: Option<i64>,
    pub task_id: i64,
    pub energy_after: Option<i64>,
    pub mood_after: Option<i64>,
    pub timestamp: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct DrawRequest {
    pub pool: String,
    pub current_energy: Option<String>,
    pub available_task_ids: Option<Vec<i64>>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct DrawChoiceResult {
    pub pool: String,
    pub choices: Vec<crate::models::task::Task>,
    pub slot_index: i64,
    pub is_urgent: bool,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlanDrawRequest {
    pub total_minutes: i64,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PlanDrawResult {
    pub pool: String,
    pub count: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct AcceptDrawRequest {
    pub task_id: i64,
    pub pool_name: String,
    pub available_time: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RejectDrawRequest {
    pub task_id: i64,
    pub reason: String,
}
