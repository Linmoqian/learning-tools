import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import shutil


DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
BACKUP_DIR = DATA_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "task_publisher.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self._add_legacy_columns()
        self._run_migrations()

    def _get_db_version(self) -> str:
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS _meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute("SELECT value FROM _meta WHERE key = 'db_version'")
        row = cursor.fetchone()
        if row:
            return row['value']
        cursor.execute("INSERT INTO _meta (key, value) VALUES ('db_version', '1.0')")
        self.conn.commit()
        return '1.0'

    def _set_db_version(self, version: str):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO _meta (key, value) VALUES ('db_version', ?)", (version,))
        self.conn.commit()

    def _backup_database(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = BACKUP_DIR / f"task_publisher_backup_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_path)
        return backup_path

    def _run_migrations(self):
        current_version = self._get_db_version()
        if current_version == '1.0':
            backup_path = self._backup_database()
            self._migrate_v1_to_v1_5()
            self._set_db_version('1.5')

    def _migrate_v1_to_v1_5(self):
        cursor = self.conn.cursor()

        v1_5_fields = [
            ("task_profile", "TEXT", "'deadline_flexible'"),
            ("parent_task_id", "INTEGER", "NULL"),
            ("group_id", "TEXT", "NULL"),
            ("last_drawn_at", "TEXT", "NULL"),
            ("draw_count_today", "INTEGER", "0"),
            ("min_push_time", "TEXT", "'20:00'"),
            ("prerequisite_ids", "TEXT", "'[]'"),
            ("is_unlocked", "INTEGER", "1"),
        ]

        for field_name, field_type, default_value in v1_5_fields:
            try:
                cursor.execute(f"ALTER TABLE tasks ADD COLUMN {field_name} {field_type} DEFAULT {default_value}")
            except sqlite3.OperationalError:
                pass

        cursor.execute("UPDATE tasks SET task_profile = 'deadline_flexible' WHERE task_profile IS NULL")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_user_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                daily_tone TEXT DEFAULT 'normal',
                energy_morning INTEGER,
                energy_afternoon INTEGER,
                energy_evening INTEGER,
                bed_time TEXT,
                sleep_early_streak INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_rejection_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_completion_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                energy_after INTEGER,
                mood_after INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        self.conn.commit()

    def _init_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                task_type TEXT DEFAULT 'other',
                description TEXT,
                estimated_time INTEGER,
                preferred_time TEXT,
                deadline TEXT,
                resistance TEXT,
                energy_required TEXT,
                rarity TEXT DEFAULT 'common',
                priority INTEGER DEFAULT 5,
                success_rate REAL DEFAULT 0.0,
                refusal_count INTEGER DEFAULT 0,
                is_daily BOOLEAN DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                prerequisite_ids TEXT DEFAULT '[]',
                is_unlocked INTEGER DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_tags (
                task_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (task_id, tag_id),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_currency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_minutes INTEGER DEFAULT 0,
                used_minutes INTEGER DEFAULT 0,
                wasted_minutes INTEGER DEFAULT 0,
                UNIQUE(date)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gacha_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                pool_name TEXT NOT NULL,
                available_time INTEGER NOT NULL,
                task_id INTEGER,
                rarity TEXT,
                accepted BOOLEAN DEFAULT 1,
                refusal_reason TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                deadline TEXT,
                estimated_time INTEGER,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_dependencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                depends_on_task_id INTEGER NOT NULL,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                energy_level TEXT,
                mood TEXT,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER,
                time_slot TEXT,
                activity TEXT,
                is_regular BOOLEAN DEFAULT 1
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_health_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condition_name TEXT NOT NULL,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rest_days (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                reason TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                chronic_conditions TEXT,
                schedule_info TEXT,
                preferences TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                actual_duration INTEGER,
                difficulty_rating INTEGER,
                notes TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                energy_level TEXT,
                mood TEXT,
                physical_condition TEXT,
                notes TEXT,
                source TEXT DEFAULT 'manual'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                available_time INTEGER,
                used_for_gacha INTEGER DEFAULT 0,
                wasted_time INTEGER DEFAULT 0,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_analysis_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                analysis_summary TEXT,
                applied_changes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                activity TEXT NOT NULL,
                notes TEXT,
                UNIQUE(date, time_slot)
            )
        ''')

        self.conn.commit()

    def _add_legacy_columns(self):
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN repeat_type TEXT DEFAULT 'none'")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN last_completed_at TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN next_available_at TEXT")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN in_discard_pile BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN completed_count INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN prerequisite_ids TEXT DEFAULT '[]'")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE tasks ADD COLUMN is_unlocked INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass
        
        self.conn.commit()

    def get_all_tags(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM tags ORDER BY name')
        rows = cursor.fetchall()
        return [row['name'] for row in rows]

    def add_tag(self, tag_name: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
        self.conn.commit()
        return cursor.lastrowid
    
    def delete_tag(self, tag_name: str):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tags WHERE name = ?', (tag_name,))
        self.conn.commit()
    
    def get_task_tags(self, task_id: int) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN task_tags tt ON t.id = tt.tag_id
            WHERE tt.task_id = ?
        ''', (task_id,))
        rows = cursor.fetchall()
        return [row['name'] for row in rows]

    def set_task_tags(self, task_id: int, tag_names: List[str]):
        cursor = self.conn.cursor()
        
        cursor.execute('DELETE FROM task_tags WHERE task_id = ?', (task_id,))
        
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            self.add_tag(tag_name)
            
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            tag_row = cursor.fetchone()
            if tag_row:
                cursor.execute(
                    'INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)',
                    (task_id, tag_row['id'])
                )
        
        self.conn.commit()

    def get_tasks_by_tag(self, tag_name: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT t.* FROM tasks t
            JOIN task_tags tt ON t.id = tt.task_id
            JOIN tags tg ON tt.tag_id = tg.id
            WHERE tg.name = ?
            ORDER BY t.id DESC
        ''', (tag_name,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_discard_pile_tasks(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE in_discard_pile = 1 AND completed = 0
            ORDER BY id DESC
        ''')
        rows = cursor.fetchall()
        tasks = [dict(row) for row in rows]
        
        for task in tasks:
            task['tags'] = self.get_task_tags(task['id'])
        
        return tasks

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            task = dict(row)
            task['tags'] = self.get_task_tags(task_id)
            return task
        return None

    def get_available_tasks_for_gacha(self) -> List[Dict]:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE completed = 0 
            AND (next_available_at IS NULL OR next_available_at <= ?)
            AND (in_discard_pile = 0 OR in_discard_pile IS NULL)
            AND is_unlocked = 1
            ORDER BY priority DESC, id ASC
        ''', (now,))
        rows = cursor.fetchall()
        tasks = [dict(row) for row in rows]
        
        for task in tasks:
            task['tags'] = self.get_task_tags(task['id'])
        
        return tasks

    def move_task_to_discard_pile(self, task_id: int):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks 
            SET in_discard_pile = 1, 
                last_completed_at = ?,
                completed_count = completed_count + 1,
                updated_at = ?
            WHERE id = ?
        ''', (now, now, task_id))
        self.conn.commit()

    def move_task_to_gacha_pile(self, task_id: int):
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE tasks 
            SET in_discard_pile = 0, updated_at = ?
            WHERE id = ?
        ''', (now, task_id))
        self.conn.commit()

    def remove_from_discard_pile(self, task_id: int):
        self.move_task_to_gacha_pile(task_id)

    def reset_daily_tasks(self):
        cursor = self.conn.cursor()
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        cursor.execute('''
            UPDATE tasks 
            SET in_discard_pile = 0,
                next_available_at = NULL,
                completed = 0,
                updated_at = ?
            WHERE repeat_type = 'daily'
            AND completed = 1
        ''', (now.isoformat(),))
        
        self.conn.commit()
        return cursor.rowcount

    def reset_weekly_tasks(self):
        cursor = self.conn.cursor()
        now = datetime.now()
        
        cursor.execute('''
            SELECT id, next_available_at FROM tasks 
            WHERE repeat_type = 'weekly' 
            AND completed = 1
        ''')
        rows = cursor.fetchall()
        
        for row in rows:
            task_id = row['id']
            next_available = row['next_available_at']
            
            if next_available and next_available <= now.isoformat():
                cursor.execute('''
                    UPDATE tasks 
                    SET in_discard_pile = 0,
                        next_available_at = NULL,
                        completed = 0,
                        updated_at = ?
                    WHERE id = ?
                ''', (now.isoformat(), task_id))
        
        self.conn.commit()
        return len(rows)

    def complete_task_with_repeat_logic(self, task_id: int) -> str:
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT repeat_type, task_type FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        if not row:
            return "task_not_found"
        
        repeat_type = row['repeat_type']
        task_type = row['task_type']
        
        now = datetime.now()
        
        if repeat_type == 'none' or task_type in ['deadline', 'other']:
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            self.conn.commit()
            return "deleted"
        
        elif repeat_type == 'daily' or task_type == 'daily':
            next_available = (now + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            
            cursor.execute('''
                UPDATE tasks 
                SET completed = 1, 
                    in_discard_pile = 1,
                    last_completed_at = ?,
                    next_available_at = ?,
                    completed_count = completed_count + 1,
                    updated_at = ?
                WHERE id = ?
            ''', (now.isoformat(), next_available, now.isoformat(), task_id))
            self.conn.commit()
            return "moved_to_discard"
        
        elif repeat_type == 'weekly' or task_type == 'weekly':
            days_until_next_week = (7 - now.weekday()) % 7
            if days_until_next_week == 0:
                days_until_next_week = 7
            
            next_available = (now + timedelta(days=days_until_next_week)).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            
            cursor.execute('''
                UPDATE tasks 
                SET completed = 1, 
                    in_discard_pile = 1,
                    last_completed_at = ?,
                    next_available_at = ?,
                    completed_count = completed_count + 1,
                    updated_at = ?
                WHERE id = ?
            ''', (now.isoformat(), next_available, now.isoformat(), task_id))
            self.conn.commit()
            return "moved_to_discard"
        
        elif repeat_type == 'accumulation' or task_type == 'accumulation':
            cursor.execute('''
                UPDATE tasks 
                SET completed = 1, 
                    in_discard_pile = 1,
                    last_completed_at = ?,
                    completed_count = completed_count + 1,
                    updated_at = ?
                WHERE id = ?
            ''', (now.isoformat(), now.isoformat(), task_id))
            self.conn.commit()
            return "moved_to_discard"
        
        else:
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            self.conn.commit()
            return "deleted"

    def add_task(self, name: str, category: str = "normal", description: str = "",
                 estimated_time: int = 30, preferred_time: str = None,
                 deadline: str = None, resistance: str = "medium",
                 energy_required: str = "medium", rarity: str = "common",
                 priority: int = 5, is_daily: bool = False, 
                 repeat_type: str = "none", tags: List[str] = None,
                 prerequisite_ids: List[int] = None) -> int:
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        if is_daily:
            repeat_type = "daily"
        
        prereq_json = json.dumps(prerequisite_ids or [])
        is_unlocked = 1 if not prerequisite_ids else 0
        
        cursor.execute('''
            INSERT INTO tasks (
                name, category, task_type, description, 
                estimated_time, preferred_time, deadline, 
                resistance, energy_required, rarity, priority,
                is_daily, repeat_type, created_at, updated_at,
                prerequisite_ids, is_unlocked
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, category, "normal", description,
            estimated_time, preferred_time, deadline,
            resistance, energy_required, rarity, priority,
            int(is_daily), repeat_type, now, now,
            prereq_json, is_unlocked
        ))
        self.conn.commit()
        
        task_id = cursor.lastrowid
        
        if tags:
            self.set_task_tags(task_id, tags)
        
        return task_id

    def get_task(self, task_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            task = dict(row)
            task['tags'] = self.get_task_tags(task_id)
            return task
        return None

    def get_task_by_name(self, task_name: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE name = ?', (task_name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def delete_task(self, task_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.conn.commit()

    def update_task(self, task_id: int, **kwargs):
        cursor = self.conn.cursor()
        
        allowed_fields = [
            'name', 'category', 'task_type', 'description', 
            'estimated_time', 'preferred_time', 'deadline',
            'resistance', 'energy_required', 'rarity', 'priority',
            'is_daily', 'repeat_type', 'difficulty'
        ]
        
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in kwargs:
                updates.append(f"{field} = ?")
                values.append(kwargs[field])
        
        if 'prerequisite_ids' in kwargs:
            updates.append("prerequisite_ids = ?")
            values.append(json.dumps(kwargs['prerequisite_ids']))
        
        if 'is_unlocked' in kwargs:
            updates.append("is_unlocked = ?")
            values.append(int(kwargs['is_unlocked']))
        
        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(task_id)
            
            cursor.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                values
            )
            self.conn.commit()
        
        if 'tags' in kwargs:
            self.set_task_tags(task_id, kwargs['tags'])

    def get_dependent_tasks(self, task_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE prerequisite_ids IS NOT NULL AND prerequisite_ids != '[]'")
        rows = cursor.fetchall()
        dependent_tasks = []
        for row in rows:
            task_dict = dict(row)
            try:
                prereq_ids = json.loads(task_dict.get('prerequisite_ids', '[]'))
                if task_id in prereq_ids:
                    task_dict['tags'] = self.get_task_tags(task_dict['id'])
                    dependent_tasks.append(task_dict)
            except (json.JSONDecodeError, TypeError):
                pass
        return dependent_tasks

    def get_all_unlocked_tasks(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE is_unlocked = 1 AND completed = 0
            AND (in_discard_pile = 0 OR in_discard_pile IS NULL)
            ORDER BY priority DESC, id ASC
        ''')
        rows = cursor.fetchall()
        tasks = [dict(row) for row in rows]
        for task in tasks:
            task['tags'] = self.get_task_tags(task['id'])
        return tasks

    def get_all_tasks_with_prerequisites(self) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks ORDER BY id ASC')
        rows = cursor.fetchall()
        tasks = [dict(row) for row in rows]
        for task in tasks:
            task['tags'] = self.get_task_tags(task['id'])
            try:
                prereq_raw = task.get('prerequisite_ids', '[]')
                task['prerequisite_ids'] = json.loads(prereq_raw) if prereq_raw else []
            except (json.JSONDecodeError, TypeError):
                task['prerequisite_ids'] = []
        return tasks

    def get_activity_options(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT name FROM activities ORDER BY name')
        rows = cursor.fetchall()
        return [row['name'] for row in rows]

    def add_activity_option(self, activity_name: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO activities (name) VALUES (?)
        ''', (activity_name,))
        self.conn.commit()

    def delete_activity_option(self, activity_name: str):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM activities WHERE name = ?', (activity_name,))
        self.conn.commit()

    def set_weekly_schedule(self, day_of_week: int, slot_id: str, activity: str, notes: str = ""):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_schedule 
            WHERE day_of_week = ? AND time_slot = ?
        ''', (day_of_week, slot_id))
        
        cursor.execute('''
            INSERT INTO user_schedule (day_of_week, time_slot, activity, is_regular)
            VALUES (?, ?, ?, 1)
        ''', (day_of_week, slot_id, activity))
        
        self.add_activity_option(activity)
        self.conn.commit()

    def set_daily_schedule(self, date: str, slot_id: str, activity: str, notes: str = ""):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_schedules (date, time_slot, activity, notes)
            VALUES (?, ?, ?, ?)
        ''', (date, slot_id, activity, notes))
        self.conn.commit()

    def get_weekly_schedule_for_day(self, day_of_week: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT time_slot, activity FROM user_schedule 
            WHERE day_of_week = ?
            ORDER BY time_slot
        ''', (day_of_week,))
        rows = cursor.fetchall()
        return [{"slot_id": row['time_slot'], "activity": row['activity']} for row in rows]

    def get_daily_schedule(self, date: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT time_slot, activity FROM daily_schedules 
            WHERE date = ?
            ORDER BY time_slot
        ''', (date,))
        rows = cursor.fetchall()
        return [{"slot_id": row['time_slot'], "activity": row['activity']} for row in rows]

    def get_schedule_slots(self) -> List[tuple]:
        default_slots = [
            ("morning1", "上午第一节", "08:00", "09:00", 1),
            ("morning2", "上午第二节", "09:00", "10:00", 2),
            ("morning3", "上午第三节", "10:00", "11:00", 3),
            ("morning4", "上午第四节", "11:00", "12:00", 4),
            ("noon", "午休", "12:00", "14:00", 5),
            ("afternoon1", "下午第一节", "14:00", "15:00", 6),
            ("afternoon2", "下午第二节", "15:00", "16:00", 7),
            ("afternoon3", "下午第三节", "16:00", "17:00", 8),
            ("afternoon4", "下午第四节", "17:00", "18:00", 9),
            ("evening", "晚自习", "18:30", "21:30", 10),
        ]
        return default_slots

    def close(self):
        self.conn.close()
