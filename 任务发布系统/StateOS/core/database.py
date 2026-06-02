# core/database.py
"""
数据库管理模块 - 终极修复版
"""

import sqlite3
import logging
from datetime import date
from pathlib import Path
from typing import Optional, Dict, Any, List


class DatabaseManager:
    """数据库管理器 - 终极修复版"""

    def __init__(self, db_path: Optional[str] = None):
        # 强制使用新的数据库文件名，确保全新开始
        if db_path is None:
            data_dir = Path.home() / ".stateos" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(data_dir / "stateos_new.db")

        self.db_path = db_path
        self.conn = None
        self.logger = logging.getLogger(__name__)

        # 立即打印信息以便调试
        print(f"[数据库] 使用数据库文件: {db_path}")

        # 不再自动初始化，而是连接现有数据库
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"[数据库] 已连接到现有数据库")

            # 只检查表是否存在，如果不存在再初始化
            if not self._check_tables_exist():
                print("[数据库] 表不存在，正在初始化...")
                self.initialize()
            else:
                print("[数据库] 表已存在，跳过初始化")

        except Exception as e:
            print(f"[数据库] 连接失败: {e}")
            import traceback
            traceback.print_exc()

    def _check_tables_exist(self) -> bool:
        """检查所有必需的表是否存在"""
        required_tables = ['daily_state', 'daily_checkins', 'activity_logs', 'state_logs']

        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]

            for table in required_tables:
                if table not in existing_tables:
                    print(f"[数据库] 缺少表: {table}")
                    return False
            return True

        except Exception as e:
            print(f"[数据库] 检查表失败: {e}")
            return False

    # ==================== 基础方法 ====================

    def get_today_date(self) -> str:
        """获取今天的日期字符串"""
        return date.today().isoformat()

    # ==================== 晨间评估相关方法 ====================

    def has_daily_checkin(self, date_str: str) -> bool:
        """检查指定日期是否有每日评估记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM daily_checkins WHERE date = ?",
                (date_str,)
            )
            count = cursor.fetchone()[0]
            print(f"[数据库] 检查晨间评估: {date_str} -> {count > 0}")
            return count > 0
        except Exception as e:
            print(f"[数据库] 检查晨间评估失败: {e}")
            return False

    def save_daily_checkin(self, checkin_data: Dict[str, Any]) -> bool:
        """保存每日评估记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO daily_checkins 
                (date, sleep_quality_initial, sleep_quality_adjusted, 
                 course_morning_1, course_morning_2, course_afternoon_1, 
                 course_afternoon_2, course_evening)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                checkin_data.get('date'),
                checkin_data.get('sleep_quality_initial', ''),
                checkin_data.get('sleep_quality_adjusted'),
                checkin_data.get('course_morning_1'),
                checkin_data.get('course_morning_2'),
                checkin_data.get('course_afternoon_1'),
                checkin_data.get('course_afternoon_2'),
                checkin_data.get('course_evening')
            ))

            self.conn.commit()
            print(f"[数据库] 保存晨间评估成功: {checkin_data.get('date')}")
            return True

        except Exception as e:
            print(f"[数据库] 保存晨间评估失败: {e}")
            return False

    # ==================== 状态日志相关方法 ====================

    def add_activity_log(self, activity_type: str, changes: dict, duration: int = None) -> bool:
        """添加活动日志"""
        try:
            cursor = self.conn.cursor()

            # 先检查表结构
            cursor.execute("PRAGMA table_info(activity_logs)")
            columns = cursor.fetchall()
            print(f"[数据库] activity_logs 表结构: {columns}")

            # 执行插入
            cursor.execute('''
                INSERT INTO activity_logs 
                (date, activity_type, energy_change, thirst_change, hunger_change, duration_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                self.get_today_date(),
                activity_type,
                changes.get('energy', 0),
                changes.get('thirst', 0),
                changes.get('hunger', 0),
                duration
            ))

            self.conn.commit()
            print(f"[数据库] 记录活动成功: {activity_type}")
            return True

        except Exception as e:
            print(f"[数据库] 记录活动失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_state_log(self, log_data: dict) -> bool:
        """保存状态日志"""
        try:
            cursor = self.conn.cursor()

            # 先检查表结构
            cursor.execute("PRAGMA table_info(state_logs)")
            columns = cursor.fetchall()
            print(f"[数据库] state_logs 表结构: {columns}")

            # 执行插入
            cursor.execute('''
                INSERT INTO state_logs 
                (date, event_type, event_detail, energy_before, energy_after, 
                 thirst_before, thirst_after, hunger_before, hunger_after)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.get_today_date(),
                log_data.get('event_type', ''),
                log_data.get('event_detail', ''),
                log_data.get('energy_before'),
                log_data.get('energy_after'),
                log_data.get('thirst_before'),
                log_data.get('thirst_after'),
                log_data.get('hunger_before'),
                log_data.get('hunger_after')
            ))

            self.conn.commit()
            print(f"[数据库] 保存状态日志成功: {log_data.get('event_type')}")
            return True

        except Exception as e:
            print(f"[数据库] 保存状态日志失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ==================== 当前状态相关方法 ====================

    # core/database.py - 修改 save_current_state() 方法

    def save_current_state(self, state_data: dict) -> bool:
        """保存当前状态 - 完整版"""
        try:
            cursor = self.conn.cursor()

            # 获取所有需要的字段
            date = state_data.get('date', self.get_today_date())
            current_energy = state_data.get('current_energy', 75)
            current_thirst = state_data.get('current_thirst', 75)
            current_hunger = state_data.get('current_hunger', 75)

            # 新增：获取其他模式字段
            high_energy_mode = state_data.get('high_energy_mode', False)
            high_energy_end_time = state_data.get('high_energy_end_time')
            low_power_mode = state_data.get('low_power_mode', False)

            print(f"[数据库] 保存完整状态: {date}")
            print(f"  精力={current_energy}, 口渴={current_thirst}, 饥饿={current_hunger}")
            print(f"  高能模式={high_energy_mode}, 低功耗模式={low_power_mode}")
            print(f"  高能结束时间={high_energy_end_time}")

            # 保存所有字段到数据库
            cursor.execute('''
                INSERT OR REPLACE INTO daily_state 
                (date, current_energy, current_thirst, current_hunger,
                 high_energy_mode, high_energy_end_time, low_power_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                date,
                current_energy,
                current_thirst,
                current_hunger,
                1 if high_energy_mode else 0,  # 转换为SQLite的布尔值
                high_energy_end_time,
                1 if low_power_mode else 0
            ))

            self.conn.commit()
            print("[数据库] 状态保存成功")
            return True

        except Exception as e:
            print(f"[数据库] 保存状态失败: {e}")
            import traceback
            traceback.print_exc()

            # 如果表结构不对，尝试重新创建表
            try:
                print("[数据库] 尝试重新创建表...")
                self.initialize()  # 重新初始化表结构
                return self.save_current_state(state_data)  # 重试
            except Exception as e2:
                print(f"[数据库] 重试也失败: {e2}")
                return False

    def get_current_state(self, date_str: str) -> Optional[dict]:
        """获取当前状态 - 完整版"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM daily_state WHERE date = ?', (date_str,))
            row = cursor.fetchone()
            if row:
                # 根据表结构：date, current_energy, current_thirst, current_hunger,
                # high_energy_mode, high_energy_end_time, low_power_mode
                result = {
                    'current_energy': row[1],
                    'current_thirst': row[2],
                    'current_hunger': row[3],
                    'high_energy_mode': bool(row[4]),  # SQLite存储为0/1
                    'high_energy_end_time': row[5],
                    'low_power_mode': bool(row[6])
                }
                print(f"[数据库] 获取完整状态成功: {date_str}")
                print(f"  结果: {result}")
                return result
            print(f"[数据库] 获取状态: {date_str} -> 无记录")
            return None
        except Exception as e:
            print(f"[数据库] 获取状态失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ==================== 其他必要方法 ====================

    def get_today_stats(self) -> Dict[str, Any]:
        """获取今日统计信息"""
        try:
            today = self.get_today_date()
            cursor = self.conn.cursor()

            stats = {
                'total_activities': 0,
                'tactical_commands': 0,
                'manual_adjustments': 0
            }

            # 获取活动总数
            cursor.execute(
                "SELECT COUNT(*) FROM activity_logs WHERE date = ?",
                (today,)
            )
            stats['total_activities'] = cursor.fetchone()[0]

            # 获取战术指令次数
            cursor.execute(
                '''SELECT COUNT(*) FROM state_logs 
                   WHERE event_type = 'tactical_command' 
                   AND date = ?''',
                (today,)
            )
            stats['tactical_commands'] = cursor.fetchone()[0]

            # 获取手动调整次数
            cursor.execute(
                '''SELECT COUNT(*) FROM state_logs 
                   WHERE event_type = 'manual_adjustment' 
                   AND date = ?''',
                (today,)
            )
            stats['manual_adjustments'] = cursor.fetchone()[0]

            print(f"[数据库] 获取统计: {stats}")
            return stats

        except Exception as e:
            print(f"[数据库] 获取统计失败: {e}")
            return {}

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("[数据库] 连接已关闭")

    # ==================== 新增方法 ====================

    def get_daily_checkin(self, date_str: str) -> Optional[Dict[str, Any]]:
        """获取指定日期的晨间评估记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM daily_checkins WHERE date = ?",
                (date_str,)
            )
            row = cursor.fetchone()

            if row:
                return {
                    'date': row[1],
                    'sleep_quality_initial': row[2],
                    'sleep_quality_adjusted': row[3],
                    'course_morning_1': row[4],
                    'course_morning_2': row[5],
                    'course_afternoon_1': row[6],
                    'course_afternoon_2': row[7],
                    'course_evening': row[8]
                }
            return None

        except Exception as e:
            print(f"[数据库] 获取晨间评估失败: {e}")
            return None

    def get_today_schedule(self) -> Dict[str, str]:
        """获取今日安排"""
        try:
            today = self.get_today_date()
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT course_morning_1, course_morning_2, course_afternoon_1, 
                       course_afternoon_2, course_evening
                FROM daily_checkins 
                WHERE date = ?
            ''', (today,))

            row = cursor.fetchone()
            if row:
                return {
                    'course_morning_1': row[0],
                    'course_morning_2': row[1],
                    'course_afternoon_1': row[2],
                    'course_afternoon_2': row[3],
                    'course_evening': row[4]
                }
            return {}

        except Exception as e:
            print(f"[数据库] 获取今日安排失败: {e}")
            return {}