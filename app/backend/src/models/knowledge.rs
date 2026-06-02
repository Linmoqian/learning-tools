use serde::{Deserialize, Serialize};

// ===== 笔记（基于 .md 文件） =====
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct Note {
    pub id: String,
    pub name: String,
    pub title: String,
    pub subject: String,
    pub tags: Vec<String>,
    pub wiki_links: Vec<String>,
    pub content: String,
    pub images: Vec<String>,
    pub created_at: String,
    pub updated_at: String,
}

// ===== 知识点（存储在 SQLite） =====
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct KnowledgePoint {
    pub id: Option<i64>,
    pub name: String,
    pub subject: String,
    pub description: String,
    pub linked_from: Vec<String>,
    pub related_points: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateKnowledgePointRequest {
    pub name: String,
    pub subject: String,
    pub description: String,
    pub related_points: Option<Vec<String>>,
}

// ===== 链接分析 =====
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct LinkIssue {
    #[serde(rename = "type")]
    pub issue_type: String,
    pub note_id: String,
    pub note_name: String,
    pub note_subject: String,
    pub target_name: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct SubjectLinkStats {
    pub notes: i64,
    pub knowledge_points: i64,
    pub links: i64,
    pub valid: i64,
    pub broken: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct LinkAnalysisResult {
    pub total_notes: i64,
    pub total_knowledge_points: i64,
    pub total_links: i64,
    pub valid_links: i64,
    pub broken_links: i64,
    pub by_subject: std::collections::HashMap<String, SubjectLinkStats>,
    pub broken_details: Vec<LinkIssue>,
    pub missing_references: Vec<String>,
    pub knowledge_point_names: Vec<String>,
}

// ===== 图谱 =====
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct GraphNode {
    pub id: String,
    pub label: String,
    pub node_type: String,
    pub subject: String,
    pub radius: i64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct GraphEdge {
    pub source: String,
    pub target: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct GraphData {
    pub nodes: Vec<GraphNode>,
    pub edges: Vec<GraphEdge>,
}

// ===== 科目统计 =====
#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct SubjectStat {
    pub name: String,
    pub color: String,
    pub note_count: i64,
    pub kp_count: i64,
    pub link_count: i64,
    pub valid_count: i64,
    pub broken_count: i64,
}

// ===== 搜索 =====
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SearchRequest {
    pub query: String,
    pub subject_filter: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct SearchResult {
    pub result_type: String,
    pub id: String,
    pub name: String,
    pub subject: String,
    pub match_field: String,
}

// ===== 创建 / 更新笔记请求 =====
#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateNoteRequest {
    pub name: String,
    pub title: String,
    pub subject: String,
    pub content: String,
    pub tags: Option<Vec<String>>,
    pub wiki_links: Option<Vec<String>>,
    pub images: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateNoteRequest {
    pub title: Option<String>,
    pub subject: Option<String>,
    pub content: Option<String>,
    pub tags: Option<Vec<String>>,
    pub wiki_links: Option<Vec<String>>,
    pub images: Option<Vec<String>>,
}

// ===== 科目常量 =====
pub const SUBJECTS: [&str; 6] = ["高数", "线代", "大物", "电子技术", "计算机", "英语四级"];

pub fn subject_color(subject: &str) -> &str {
    match subject {
        "高数" => "#e74c3c",
        "线代" => "#9b59b6",
        "大物" => "#3498db",
        "电子技术" => "#e67e22",
        "计算机" => "#2ecc71",
        "英语四级" => "#f1c40f",
        _ => "#666666",
    }
}
