import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ..models.database import Database


class ExportService:
    def __init__(self, db: Database):
        self.db = db
        self.export_dir = Path("./ai_exports")
        self.export_dir.mkdir(exist_ok=True)

    def export_all_data(self) -> str:
        data = {
            "export_metadata": {
                "export_date": datetime.now().isoformat(),
                "system": "任务随机发布器",
                "version": "1.0"
            },
            "user_profile": self._get_user_profile(),
            "tasks": self._get_all_tasks(),
            "gacha_records": self._get_gacha_records(),
            "task_completions": self._get_task_completions(),
            "user_states": self._get_user_states(),
            "time_logs": self._get_time_logs(),
            "rest_days": self._get_rest_days()
        }
        
        filename = f"ai_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(filepath)

    def _get_user_profile(self) -> Dict:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM user_profile LIMIT 1')
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {}

    def _get_all_tasks(self) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_gacha_records(self, limit: int = 100) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM gacha_records 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_task_completions(self, limit: int = 100) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM task_completions 
            ORDER BY completed_at DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_user_states(self, limit: int = 100) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM user_states 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_time_logs(self, limit: int = 30) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM time_logs 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def _get_rest_days(self, limit: int = 30) -> list:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM rest_days 
            ORDER BY date DESC 
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
