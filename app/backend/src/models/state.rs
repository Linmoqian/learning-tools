use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct DailyUserState {
    pub id: Option<i64>,
    pub date: String,
    pub daily_tone: String,
    pub energy_morning: Option<i64>,
    pub energy_afternoon: Option<i64>,
    pub energy_evening: Option<i64>,
    pub bed_time: Option<String>,
    pub sleep_early_streak: i64,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SetDailyStateRequest {
    pub date: String,
    pub daily_tone: Option<String>,
    pub energy_morning: Option<i64>,
    pub energy_afternoon: Option<i64>,
    pub energy_evening: Option<i64>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct RecordSleepRequest {
    pub date: String,
    pub bed_time: String,
    pub on_time: bool,
}
