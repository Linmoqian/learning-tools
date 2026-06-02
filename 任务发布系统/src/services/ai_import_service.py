import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from ..models.database import Database


class AIImportService:
    def __init__(self, db: Database):
        self.db = db
        self.import_dir = Path("./ai_imports")
        self.import_dir.mkdir(exist_ok=True)

    def scan_import_files(self) -> List[Dict]:
        files = []
        for filepath in self.import_dir.glob("ai_analysis_*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    files.append({
                        "filename": filepath.name,
                        "filepath": str(filepath),
                        "data": data,
                        "analysis_date": data.get("analysis_metadata", {}).get("analysis_date", "未知")
                    })
            except Exception as e:
                files.append({
                    "filename": filepath.name,
                    "filepath": str(filepath),
                    "error": str(e)
                })
        return files

    def import_analysis(self, filepath: str) -> Dict:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cursor = self.db.conn.cursor()
        
        summary = data.get("summary", {})
        task_adjustments = data.get("task_adjustments", [])
        weight_adjustments = data.get("weight_adjustments", {})
        user_insights = data.get("user_insights", [])
        suggested_new_tasks = data.get("suggested_new_tasks", [])
        
        applied_changes = {
            "task_adjustments": [],
            "new_tasks_added": [],
            "weight_adjustments": weight_adjustments
        }
        
        for adjustment in task_adjustments:
            if adjustment.get("applied"):
                task_id = adjustment.get("task_id")
                suggestions = adjustment.get("suggestions", {})
                
                if task_id and suggestions:
                    self._apply_task_adjustment(task_id, suggestions)
                    applied_changes["task_adjustments"].append({
                        "task_id": task_id,
                        "applied_suggestions": suggestions
                    })
        
        for new_task in suggested_new_tasks:
            if new_task.get("applied"):
                self._add_suggested_task(new_task)
                applied_changes["new_tasks_added"].append(new_task.get("name"))
        
        cursor.execute('''
            INSERT INTO ai_analysis_imports (file_path, analysis_summary, applied_changes)
            VALUES (?, ?, ?)
        ''', (
            filepath,
            f"分析了 {summary.get('total_tasks', 0)} 个任务，成功率 {summary.get('completion_rate', 0)}",
            json.dumps(applied_changes, ensure_ascii=False)
        ))
        self.db.conn.commit()
        
        self._delete_file(filepath)
        
        return {
            "success": True,
            "applied_changes": applied_changes,
            "user_insights": user_insights
        }

    def _apply_task_adjustment(self, task_id: int, suggestions: Dict):
        cursor = self.db.conn.cursor()
        
        updates = []
        values = []
        
        if "change_rarity_to" in suggestions:
            updates.append("rarity = ?")
            values.append(suggestions["change_rarity_to"])
        
        if "change_resistance_to" in suggestions:
            updates.append("resistance = ?")
            values.append(suggestions["change_resistance_to"])
        
        if "change_priority_to" in suggestions:
            updates.append("priority = ?")
            values.append(suggestions["change_priority_to"])
        
        if updates:
            values.append(task_id)
            sql = f"UPDATE tasks SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            cursor.execute(sql, values)
            self.db.conn.commit()

    def _add_suggested_task(self, task_data: Dict):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (
                name, category, task_type, description, 
                estimated_time, resistance, energy_required, 
                rarity, priority, is_daily
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data.get("name", ""),
            task_data.get("category", "other"),
            task_data.get("task_type", "other"),
            task_data.get("description"),
            task_data.get("estimated_time", 25),
            task_data.get("resistance", "medium"),
            task_data.get("energy_required", "medium"),
            task_data.get("rarity", "common"),
            task_data.get("priority", 5),
            task_data.get("is_daily", False)
        ))
        self.db.conn.commit()

    def get_import_history(self) -> List[Dict]:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM ai_analysis_imports 
            ORDER BY timestamp DESC 
            LIMIT 20
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def _delete_file(self, filepath: str):
        try:
            file_path = Path(filepath)
            if file_path.exists():
                file_path.unlink()
                print(f"已删除文件: {filepath}")
            else:
                print(f"文件不存在: {filepath}")
        except Exception as e:
            print(f"删除文件失败 {filepath}: {e}")
