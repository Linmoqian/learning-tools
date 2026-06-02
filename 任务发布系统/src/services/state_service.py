from typing import Optional, List, Dict
from datetime import datetime, date, timedelta
import sqlite3

from ..models.database import Database


class DailyTone:
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    REST = "rest"


class EnergyPeriod:
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class StateService:
    def __init__(self, db: Database):
        self.db = db

    def set_daily_tone(self, tone: str, target_date: Optional[date] = None) -> int:
        target_date = target_date or date.today()
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_user_state (date, daily_tone)
            VALUES (?, ?)
        ''', (target_date.isoformat(), tone))
        self.db.conn.commit()
        return cursor.lastrowid

    def get_daily_tone(self, target_date: Optional[date] = None) -> str:
        target_date = target_date or date.today()
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT daily_tone FROM daily_user_state WHERE date = ?
        ''', (target_date.isoformat(),))
        row = cursor.fetchone()
        if row:
            return row['daily_tone']
        return DailyTone.NORMAL

    def get_energy_adjustment(self, target_date: Optional[date] = None) -> int:
        tone = self.get_daily_tone(target_date)
        if tone == DailyTone.LOW:
            return -2
        elif tone == DailyTone.HIGH:
            return 1
        return 0

    def is_rest_day(self, target_date: Optional[date] = None) -> bool:
        return self.get_daily_tone(target_date) == DailyTone.REST

    def record_period_energy(self, period: str, energy: int,
                             target_date: Optional[date] = None) -> int:
        target_date = target_date or date.today()
        cursor = self.db.conn.cursor()

        cursor.execute('SELECT id FROM daily_user_state WHERE date = ?', (target_date.isoformat(),))
        existing = cursor.fetchone()

        field_map = {
            EnergyPeriod.MORNING: 'energy_morning',
            EnergyPeriod.AFTERNOON: 'energy_afternoon',
            EnergyPeriod.EVENING: 'energy_evening',
        }
        field = field_map.get(period)
        if not field:
            return 0

        if existing:
            cursor.execute(f'''
                UPDATE daily_user_state SET {field} = ? WHERE date = ?
            ''', (energy, target_date.isoformat()))
        else:
            cursor.execute(f'''
                INSERT INTO daily_user_state (date, {field})
                VALUES (?, ?)
            ''', (target_date.isoformat(), energy))

        self.db.conn.commit()
        return cursor.lastrowid

    def get_period_energy(self, period: str,
                          target_date: Optional[date] = None) -> Optional[int]:
        target_date = target_date or date.today()
        field_map = {
            EnergyPeriod.MORNING: 'energy_morning',
            EnergyPeriod.AFTERNOON: 'energy_afternoon',
            EnergyPeriod.EVENING: 'energy_evening',
        }
        field = field_map.get(period)
        if not field:
            return None

        cursor = self.db.conn.cursor()
        cursor.execute(f'SELECT {field} FROM daily_user_state WHERE date = ?',
                       (target_date.isoformat(),))
        row = cursor.fetchone()
        if row and row[field] is not None:
            return row[field]
        return None

    def get_average_energy_by_hour(self) -> Dict[int, float]:
        cursor = self.db.conn.cursor()
        seven_days_ago = (date.today() - timedelta(days=7)).isoformat()

        cursor.execute('''
            SELECT energy_morning, energy_afternoon, energy_evening
            FROM daily_user_state
            WHERE date >= ?
              AND (energy_morning IS NOT NULL
                OR energy_afternoon IS NOT NULL
                OR energy_evening IS NOT NULL)
        ''', (seven_days_ago,))

        rows = cursor.fetchall()
        if not rows:
            return {}

        total_morning = 0
        total_afternoon = 0
        total_evening = 0
        count_morning = 0
        count_afternoon = 0
        count_evening = 0

        for row in rows:
            if row['energy_morning'] is not None:
                total_morning += row['energy_morning']
                count_morning += 1
            if row['energy_afternoon'] is not None:
                total_afternoon += row['energy_afternoon']
                count_afternoon += 1
            if row['energy_evening'] is not None:
                total_evening += row['energy_evening']
                count_evening += 1

        energy_map = {}
        if count_morning > 0:
            energy_map[8] = round(total_morning / count_morning, 1)
            energy_map[9] = round(total_morning / count_morning, 1)
            energy_map[10] = round(total_morning / count_morning, 1)
            energy_map[11] = round(total_morning / count_morning, 1)
        if count_afternoon > 0:
            avg = total_afternoon / count_afternoon
            energy_map[14] = round(avg, 1)
            energy_map[15] = round(avg, 1)
            energy_map[16] = round(avg, 1)
            energy_map[17] = round(avg, 1)
        if count_evening > 0:
            avg = total_evening / count_evening
            energy_map[19] = round(avg, 1)
            energy_map[20] = round(avg, 1)
            energy_map[21] = round(avg, 1)

        return energy_map

    def record_sleep_time(self, bed_time: str, sleep_quality: Optional[str] = None,
                          target_date: Optional[date] = None) -> int:
        target_date = target_date or date.today()
        cursor = self.db.conn.cursor()

        cursor.execute('SELECT id, sleep_early_streak FROM daily_user_state WHERE date = ?',
                       (target_date.isoformat(),))
        existing = cursor.fetchone()

        if existing:
            new_streak = existing['sleep_early_streak'] or 0
            if sleep_quality == "on_time":
                new_streak += 1
            else:
                new_streak = 0

            cursor.execute('''
                UPDATE daily_user_state
                SET bed_time = ?, sleep_early_streak = ?
                WHERE date = ?
            ''', (bed_time, new_streak, target_date.isoformat()))
        else:
            new_streak = 1 if sleep_quality == "on_time" else 0
            cursor.execute('''
                INSERT INTO daily_user_state (date, bed_time, sleep_early_streak)
                VALUES (?, ?, ?)
            ''', (target_date.isoformat(), bed_time, new_streak))

        self.db.conn.commit()
        return cursor.lastrowid

    def get_sleep_early_streak(self) -> int:
        cursor = self.db.conn.cursor()
        today = date.today().isoformat()
        cursor.execute('''
            SELECT sleep_early_streak FROM daily_user_state
            WHERE date = ? AND sleep_early_streak IS NOT NULL
        ''', (today,))
        row = cursor.fetchone()
        if row:
            return row['sleep_early_streak']
        return 0

    def record_state(self, energy_level: str, mood: Optional[str] = None,
                     notes: Optional[str] = None) -> int:
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO user_state (energy_level, mood, notes)
            VALUES (?, ?, ?)
        ''', (energy_level, mood, notes))
        self.db.conn.commit()
        return cursor.lastrowid

    def get_latest_state(self) -> Optional[Dict]:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM user_state ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_overdue_tasks(self) -> List[Dict]:
        cursor = self.db.conn.cursor()
        today = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM tasks
            WHERE completed = 0 AND deadline IS NOT NULL AND deadline < ?
            ORDER BY deadline ASC
        ''', (today,))
        return [dict(row) for row in cursor.fetchall()]

    def get_daily_state_summary(self, target_date: Optional[date] = None) -> Dict:
        target_date = target_date or date.today()
        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT * FROM daily_user_state WHERE date = ?
        ''', (target_date.isoformat(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return {
            "date": target_date.isoformat(),
            "daily_tone": DailyTone.NORMAL,
            "energy_morning": None,
            "energy_afternoon": None,
            "energy_evening": None,
            "bed_time": None,
            "sleep_early_streak": 0,
        }