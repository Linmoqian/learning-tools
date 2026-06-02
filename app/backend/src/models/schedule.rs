use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ScheduleSlot {
    pub slot_id: String,
    pub slot_name: String,
    pub start_time: String,
    pub end_time: String,
    pub display_order: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ScheduleItem {
    pub id: Option<i64>,
    pub date: String,
    pub slot_id: String,
    pub activity: String,
    pub notes: Option<String>,
    pub schedule_type: String,
    pub day_of_week: Option<i64>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SetScheduleRequest {
    pub date: String,
    pub slot_id: String,
    pub activity: String,
    pub notes: Option<String>,
    pub schedule_type: Option<String>,
    pub day_of_week: Option<i64>,
}

pub fn default_slots() -> Vec<ScheduleSlot> {
    vec![
        ScheduleSlot { slot_id: "morning1".into(),    slot_name: "上午第一节".into(), start_time: "08:00".into(),  end_time: "09:00".into(),  display_order: 1 },
        ScheduleSlot { slot_id: "morning2".into(),    slot_name: "上午第二节".into(), start_time: "09:00".into(),  end_time: "10:00".into(),  display_order: 2 },
        ScheduleSlot { slot_id: "morning3".into(),    slot_name: "上午第三节".into(), start_time: "10:00".into(),  end_time: "11:00".into(),  display_order: 3 },
        ScheduleSlot { slot_id: "morning4".into(),    slot_name: "上午第四节".into(), start_time: "11:00".into(),  end_time: "12:00".into(),  display_order: 4 },
        ScheduleSlot { slot_id: "noon".into(),        slot_name: "午休".into(),        start_time: "12:00".into(),  end_time: "14:00".into(),  display_order: 5 },
        ScheduleSlot { slot_id: "afternoon1".into(),  slot_name: "下午第一节".into(), start_time: "14:00".into(),  end_time: "15:00".into(),  display_order: 6 },
        ScheduleSlot { slot_id: "afternoon2".into(),  slot_name: "下午第二节".into(), start_time: "15:00".into(),  end_time: "16:00".into(),  display_order: 7 },
        ScheduleSlot { slot_id: "afternoon3".into(),  slot_name: "下午第三节".into(), start_time: "16:00".into(),  end_time: "17:00".into(),  display_order: 8 },
        ScheduleSlot { slot_id: "afternoon4".into(),  slot_name: "下午第四节".into(), start_time: "17:00".into(),  end_time: "18:00".into(),  display_order: 9 },
        ScheduleSlot { slot_id: "evening".into(),     slot_name: "晚自习".into(),      start_time: "18:30".into(),  end_time: "21:30".into(),  display_order: 10 },
    ]
}
