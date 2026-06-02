use crate::models::knowledge::*;
use chrono::Utc;
use regex::Regex;
use std::collections::HashMap;
use std::fs;
use std::path::Path;

// ===== 从 .md 文件解析 frontmatter 和内容 =====
fn parse_md_file(path: &Path) -> Option<Note> {
    let content = fs::read_to_string(path).ok()?;
    let file_stem = path.file_stem()?.to_str()?.to_string();
    let name = file_stem;

    // 解析 YAML frontmatter (---...---)
    let (frontmatter, body) = if content.starts_with("---") {
        if let Some(end) = content[3..].find("\n---") {
            let yaml = &content[3..3 + end];
            let body_start = 3 + end + 5; // skip "---\n" + yaml + "\n---\n"
            (Some(yaml), &content[body_start..])
        } else {
            (None, content.as_str())
        }
    } else {
        (None, content.as_str())
    };

    let body = body.trim();

    // 解析 frontmatter 字段
    let mut title = name.clone();
    let mut subject = String::from("计算机");
    let mut tags: Vec<String> = Vec::new();
    let mut images: Vec<String> = Vec::new();
    let mut created_at = Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();
    let mut updated_at = created_at.clone();

    if let Some(yaml) = frontmatter {
        for line in yaml.lines() {
            if let Some(val) = line.strip_prefix("title:") {
                title = val.trim().trim_matches('"').to_string();
            } else if let Some(val) = line.strip_prefix("subject:") {
                subject = val.trim().trim_matches('"').to_string();
                if !SUBJECTS.contains(&subject.as_str()) {
                    subject = String::from("计算机");
                }
            } else if let Some(val) = line.strip_prefix("tags:") {
                // tags: [a, b, c] or tags: [a, b, c]
                let val = val.trim();
                if val.starts_with('[') && val.ends_with(']') {
                    let inner = &val[1..val.len() - 1];
                    for item in inner.split(',') {
                        let t = item.trim().trim_matches('"');
                        if !t.is_empty() {
                            tags.push(t.to_string());
                        }
                    }
                }
            } else if let Some(val) = line.strip_prefix("images:") {
                let val = val.trim();
                if val.starts_with('[') && val.ends_with(']') {
                    let inner = &val[1..val.len() - 1];
                    for item in inner.split(',') {
                        let img = item.trim().trim_matches('"');
                        if !img.is_empty() {
                            images.push(img.to_string());
                        }
                    }
                }
            } else if let Some(val) = line.strip_prefix("created_at:") {
                created_at = val.trim().trim_matches('"').to_string();
            } else if let Some(val) = line.strip_prefix("updated_at:") {
                updated_at = val.trim().trim_matches('"').to_string();
            }
        }
    }

    // 从 body 提取 wikiLinks: [[name]]
    let re = Regex::new(r"\[\[([^\]]+)\]\]").unwrap();
    let wiki_links: Vec<String> = re
        .captures_iter(body)
        .map(|c| c[1].trim().to_string())
        .filter(|s| !s.is_empty())
        .collect::<std::collections::HashSet<_>>()
        .into_iter()
        .collect();

    Some(Note {
        id: format!("note_{}", &name.replace(|c: char| !c.is_alphanumeric(), "_")),
        name,
        title,
        subject,
        tags,
        wiki_links,
        content: body.to_string(),
        images,
        created_at,
        updated_at,
    })
}

// ===== 扫描笔记目录 =====
pub fn scan_notes_dir(notes_dir: &Path) -> Vec<Note> {
    if !notes_dir.exists() {
        fs::create_dir_all(notes_dir).ok();
        return vec![];
    }

    let mut notes = Vec::new();
    if let Ok(entries) = fs::read_dir(notes_dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.extension().and_then(|s| s.to_str()) == Some("md") {
                if let Some(note) = parse_md_file(&path) {
                    notes.push(note);
                }
            }
        }
    }
    notes.sort_by(|a, b| a.name.cmp(&b.name));
    notes
}

// ===== 写笔记为 .md 文件 =====
pub fn write_note_file(notes_dir: &Path, note: &Note) -> Result<String, String> {
    let path = notes_dir.join(format!("{}.md", note.name));

    // 构建 frontmatter
    let tags_str = if note.tags.is_empty() {
        String::new()
    } else {
        let items: Vec<String> = note.tags.iter().map(|t| format!("\"{}\"", t)).collect();
        format!("\ntags: [{}]", items.join(", "))
    };
    let images_str = if note.images.is_empty() {
        String::new()
    } else {
        let items: Vec<String> = note.images.iter().map(|i| format!("\"{}\"", i)).collect();
        format!("\nimages: [{}]", items.join(", "))
    };

    let frontmatter = format!(
        "---\ntitle: {}{}\nsubject: {}{}{}\ncreated_at: {}\nupdated_at: {}\n---\n\n{}",
        note.title,
        tags_str,
        note.subject,
        images_str,
        if !note.tags.is_empty() || !note.images.is_empty() { "" } else { "" },
        note.created_at,
        note.updated_at,
        note.content
    );

    fs::write(&path, &frontmatter).map_err(|e| format!("写入文件失败: {}", e))?;
    Ok(note.id.clone())
}

// ===== 删除笔记文件 =====
pub fn delete_note_file(notes_dir: &Path, name: &str) -> Result<(), String> {
    let path = notes_dir.join(format!("{}.md", name));
    if path.exists() {
        fs::remove_file(&path).map_err(|e| format!("删除文件失败: {}", e))
    } else {
        Err("文件不存在".into())
    }
}

// ===== 链接分析算法（匹配前端 knowledge.ts analyzeLinks） =====
pub fn analyze_links(notes: &[Note], knowledge_points: &[KnowledgePoint]) -> LinkAnalysisResult {
    let kp_names: std::collections::HashSet<&str> =
        knowledge_points.iter().map(|kp| kp.name.as_str()).collect();

    let mut by_subject: HashMap<String, SubjectLinkStats> = HashMap::new();
    for s in SUBJECTS.iter() {
        by_subject.insert(
            s.to_string(),
            SubjectLinkStats {
                notes: 0,
                knowledge_points: 0,
                links: 0,
                valid: 0,
                broken: 0,
            },
        );
    }

    let mut broken_details = Vec::new();
    let mut missing_refs = std::collections::HashSet::new();
    let mut total_links = 0i64;
    let mut valid_links = 0i64;

    for note in notes {
        if let Some(stats) = by_subject.get_mut(&note.subject) {
            stats.notes += 1;
        }

        for link in &note.wiki_links {
            total_links += 1;
            if let Some(stats) = by_subject.get_mut(&note.subject) {
                stats.links += 1;
            }

            if kp_names.contains(link.as_str()) {
                valid_links += 1;
                if let Some(stats) = by_subject.get_mut(&note.subject) {
                    stats.valid += 1;
                }
            } else {
                if let Some(stats) = by_subject.get_mut(&note.subject) {
                    stats.broken += 1;
                }
                missing_refs.insert(link.clone());
                broken_details.push(LinkIssue {
                    issue_type: String::from("broken_link"),
                    note_id: note.id.clone(),
                    note_name: note.title.clone(),
                    note_subject: note.subject.clone(),
                    target_name: link.clone(),
                });
            }
        }
    }

    // 统计每个科目的知识点数量
    for kp in knowledge_points {
        if let Some(stats) = by_subject.get_mut(&kp.subject) {
            stats.knowledge_points += 1;
        }
    }

    let kp_name_list: Vec<String> = knowledge_points.iter().map(|kp| kp.name.clone()).collect();
    let mut missing: Vec<String> = missing_refs.into_iter().collect();
    missing.sort();

    LinkAnalysisResult {
        total_notes: notes.len() as i64,
        total_knowledge_points: knowledge_points.len() as i64,
        total_links,
        valid_links,
        broken_links: broken_details.len() as i64,
        by_subject,
        broken_details,
        missing_references: missing,
        knowledge_point_names: kp_name_list,
    }
}

// ===== 构建图谱（匹配前端 knowledge.ts buildGraph） =====
pub fn build_graph(notes: &[Note], knowledge_points: &[KnowledgePoint]) -> GraphData {
    let mut nodes: Vec<GraphNode> = Vec::new();
    let mut edges: Vec<GraphEdge> = Vec::new();
    let mut seen_ids = std::collections::HashSet::new();

    for note in notes {
        if !seen_ids.insert(note.id.clone()) {
            continue;
        }
        let label = if note.title.chars().count() > 8 {
            format!("{}…", note.title.chars().take(8).collect::<String>())
        } else {
            note.title.clone()
        };
        nodes.push(GraphNode {
            id: note.id.clone(),
            label,
            node_type: String::from("note"),
            subject: note.subject.clone(),
            radius: 18,
        });
    }

    let kp_id_map: HashMap<&str, &KnowledgePoint> =
        knowledge_points.iter().map(|kp| (kp.name.as_str(), kp)).collect();

    for kp in knowledge_points {
        let kp_id = format!("kp_{}", kp.name.replace(|c: char| !c.is_alphanumeric(), "_"));
        if !seen_ids.insert(kp_id.clone()) {
            continue;
        }
        let label = if kp.name.chars().count() > 6 {
            format!("{}…", kp.name.chars().take(6).collect::<String>())
        } else {
            kp.name.clone()
        };
        nodes.push(GraphNode {
            id: kp_id,
            label,
            node_type: String::from("knowledge"),
            subject: kp.subject.clone(),
            radius: 14,
        });
    }

    for note in notes {
        for link in &note.wiki_links {
            if let Some(kp) = kp_id_map.get(link.as_str()) {
                let kp_id = format!("kp_{}", kp.name.replace(|c: char| !c.is_alphanumeric(), "_"));
                edges.push(GraphEdge {
                    source: note.id.clone(),
                    target: kp_id,
                });
            }
        }
    }

    GraphData { nodes, edges }
}

// ===== 搜索（匹配前端 knowledge.ts searchItems） =====
pub fn search_items(
    notes: &[Note],
    knowledge_points: &[KnowledgePoint],
    query: &str,
    subject_filter: Option<&str>,
) -> Vec<SearchResult> {
    let q = query.to_lowercase().trim().to_string();
    if q.is_empty() {
        return vec![];
    }

    let mut results = Vec::new();

    for note in notes {
        if let Some(sf) = subject_filter {
            if note.subject != sf {
                continue;
            }
        }
        if note.title.to_lowercase().contains(&q)
            || note.name.to_lowercase().contains(&q)
            || note.content.to_lowercase().contains(&q)
        {
            results.push(SearchResult {
                result_type: String::from("note"),
                id: note.id.clone(),
                name: note.title.clone(),
                subject: note.subject.clone(),
                match_field: String::from("标题/内容"),
            });
        }
    }

    for kp in knowledge_points {
        if let Some(sf) = subject_filter {
            if kp.subject != sf {
                continue;
            }
        }
        if kp.name.to_lowercase().contains(&q) || kp.description.to_lowercase().contains(&q) {
            results.push(SearchResult {
                result_type: String::from("knowledge"),
                id: format!("kp_{}", kp.name.replace(|c: char| !c.is_alphanumeric(), "_")),
                name: kp.name.clone(),
                subject: kp.subject.clone(),
                match_field: String::from("名称/描述"),
            });
        }
    }

    results
}

// ===== 科目统计 =====
pub fn get_subject_stats(analysis: &LinkAnalysisResult) -> Vec<SubjectStat> {
    SUBJECTS
        .iter()
        .map(|name| {
            let s = analysis
                .by_subject
                .get(*name)
                .cloned()
                .unwrap_or(SubjectLinkStats {
                    notes: 0,
                    knowledge_points: 0,
                    links: 0,
                    valid: 0,
                    broken: 0,
                });
            let color = subject_color(name);
            SubjectStat {
                name: name.to_string(),
                color: color.to_string(),
                note_count: s.notes,
                kp_count: s.knowledge_points,
                link_count: s.links,
                valid_count: s.valid,
                broken_count: s.broken,
            }
        })
        .collect()
}
