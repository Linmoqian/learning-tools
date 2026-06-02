from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta, date
import random
import math
import json

from ..models.database import Database
from ..models.task import Task, Resistance, EnergyRequired, TaskProfile, RepeatType


class TaskService:
    def __init__(self, db: Database):
        self.db = db

    def add_task(self, task: Task) -> int:
        return self.db.add_task(
            name=task.name,
            category=task.category,
            description=task.description or "",
            estimated_time=task.estimated_time or 30,
            preferred_time=task.preferred_time,
            deadline=task.deadline,
            resistance=task.resistance,
            energy_required=task.energy_required,
            rarity=task.rarity,
            priority=task.priority,
            is_daily=task.is_daily,
            repeat_type=task.repeat_type,
            tags=task.tags,
            prerequisite_ids=task.prerequisite_ids
        )

    def get_task(self, task_id: int) -> Optional[Task]:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        if row:
            return Task.from_row(row)
        return None

    def get_all_tasks(self, include_completed: bool = False) -> List[Task]:
        cursor = self.db.conn.cursor()
        if include_completed:
            cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC')
        else:
            cursor.execute('SELECT * FROM tasks WHERE completed = 0 ORDER BY created_at DESC')
        rows = cursor.fetchall()
        return [Task.from_row(row) for row in rows]

    def update_task(self, task: Task):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            UPDATE tasks
            SET name=?, category=?, task_type=?, description=?, estimated_time=?,
                preferred_time=?, deadline=?, resistance=?, energy_required=?,
                rarity=?, priority=?, success_rate=?, refusal_count=?,
                is_daily=?, completed=?, repeat_type=?, task_profile=?,
                parent_task_id=?, group_id=?, min_push_time=?, difficulty=?,
                prerequisite_ids=?, is_unlocked=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            task.name,
            task.category,
            task.task_type,
            task.description,
            task.estimated_time,
            task.preferred_time,
            task.deadline,
            task.resistance,
            task.energy_required,
            task.rarity,
            task.priority,
            task.success_rate,
            task.refusal_count,
            task.is_daily,
            task.completed,
            task.repeat_type,
            task.task_profile,
            task.parent_task_id,
            task.group_id,
            task.min_push_time,
            task.difficulty,
            json.dumps(task.prerequisite_ids),
            int(task.is_unlocked),
            task.id
        ))
        self.db.conn.commit()

        if task.tags:
            self.db.set_task_tags(task.id, task.tags)

    def delete_task(self, task_id: int):
        cursor = self.db.conn.cursor()
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        self.db.conn.commit()

    def detect_cycle(self, task_id: int, proposed_prerequisite_ids: List[int]) -> bool:
        if not proposed_prerequisite_ids:
            return False

        visited = set()

        def dfs(current_id: int) -> bool:
            if current_id == task_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)
            task_dict = self.db.get_task(current_id)
            if not task_dict:
                return False
            try:
                prereq_raw = task_dict.get('prerequisite_ids', '[]')
                prereq_ids = json.loads(prereq_raw) if prereq_raw else []
            except (json.JSONDecodeError, TypeError):
                prereq_ids = []
            for pid in prereq_ids:
                if dfs(pid):
                    return True
            return False

        for pid in proposed_prerequisite_ids:
            if dfs(pid):
                return True
        return False

    def _check_all_prerequisites_completed(self, task_dict: dict) -> bool:
        try:
            prereq_raw = task_dict.get('prerequisite_ids', '[]')
            prereq_ids = json.loads(prereq_raw) if prereq_raw else []
        except (json.JSONDecodeError, TypeError):
            prereq_ids = []
        if not prereq_ids:
            return True
        for pid in prereq_ids:
            prereq = self.db.get_task(pid)
            if not prereq or not prereq.get('completed'):
                return False
        return True

    def mark_completed(self, task_id: int) -> List[str]:
        cursor = self.db.conn.cursor()
        cursor.execute('UPDATE tasks SET completed = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (task_id,))

        task = self.get_task(task_id)
        if task:
            new_success_rate = min(1.0, task.success_rate + 0.1)
            cursor.execute('UPDATE tasks SET success_rate = ? WHERE id = ?', (new_success_rate, task_id))

        self.db.conn.commit()

        return self._chain_unlock(task_id)

    def skip_task(self, task_id: int) -> List[str]:
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE tasks SET completed = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (task_id,))
        self.db.conn.commit()

        return self._chain_unlock(task_id)

    def _chain_unlock(self, task_id: int) -> List[str]:
        unlocked_names = []
        dependent_dicts = self.db.get_dependent_tasks(task_id)

        for dep_dict in dependent_dicts:
            dep_id = dep_dict['id']
            if self._check_all_prerequisites_completed(dep_dict):
                cursor = self.db.conn.cursor()
                cursor.execute("UPDATE tasks SET is_unlocked = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (dep_id,))
                self.db.conn.commit()
                unlocked_names.append(dep_dict['name'])
                nested_unlocked = self._chain_unlock(dep_id)
                unlocked_names.extend(nested_unlocked)

        return unlocked_names

    def get_first_unlocked_in_chain(self, task_id: int) -> Optional[Task]:
        task_dict = self.db.get_task(task_id)
        if not task_dict:
            return None

        if task_dict.get('is_unlocked', 0) and not task_dict.get('completed'):
            return self.get_task(task_id)

        try:
            prereq_raw = task_dict.get('prerequisite_ids', '[]')
            prereq_ids = json.loads(prereq_raw) if prereq_raw else []
        except (json.JSONDecodeError, TypeError):
            prereq_ids = []

        if not prereq_ids:
            return None

        for pid in prereq_ids:
            result = self.get_first_unlocked_in_chain(pid)
            if result:
                return result
        return None

    def record_refusal(self, task_id: int):
        cursor = self.db.conn.cursor()
        task = self.get_task(task_id)
        if task:
            cursor.execute('UPDATE tasks SET refusal_count = refusal_count + 1 WHERE id = ?', (task_id,))
        self.db.conn.commit()

    def get_top_weighted_tasks(self, tasks: List[Task], n: int = 3,
                                current_energy: str = Resistance.MEDIUM.value,
                                session_context: Optional[Dict] = None) -> List[Task]:
        if not tasks:
            return []

        weights = [self._calculate_full_weight(task, current_energy, session_context) for task in tasks]

        total_weight = sum(weights)
        if total_weight <= 0:
            return random.choices(tasks, k=n)

        result = []
        for _ in range(n):
            random_val = random.random() * total_weight
            cumulative = 0.0
            for task, weight in zip(tasks, weights):
                cumulative += weight
                if cumulative >= random_val:
                    result.append(task)
                    break

        return result

    def select_weighted_random_task(self, current_energy: str = Resistance.MEDIUM.value,
                                    session_context: Optional[Dict] = None) -> Optional[Task]:
        tasks = self.get_all_tasks(include_completed=False)

        tasks = [t for t in tasks if t.task_profile != TaskProfile.DAILY_HABIT.value]

        if not tasks:
            return None

        weights = []
        for task in tasks:
            weight = self._calculate_full_weight(task, current_energy, session_context)
            weights.append(weight)

        total_weight = sum(weights)
        if total_weight <= 0:
            return random.choice(tasks)

        random_val = random.random() * total_weight
        cumulative = 0.0
        for task, weight in zip(tasks, weights):
            cumulative += weight
            if cumulative >= random_val:
                return task
        return tasks[-1]

    def _calculate_full_weight(self, task: Task, current_energy: str,
                                session_context: Optional[Dict] = None) -> float:
        weight = 1.0

        weight *= self._calculate_priority_weight(task)
        weight *= self._calculate_deadline_urgency(task)
        weight *= self._calculate_energy_match(task, current_energy)
        weight *= self._calculate_resistance_factor(task)
        weight *= self._calculate_success_rate_factor(task)
        weight *= self._calculate_refusal_penalty(task)
        weight *= self._calculate_profile_strategy_weight(task)

        if session_context:
            weight *= self._calculate_cooldown_factor(task, session_context)

        weight = float(weight)
        return max(0.01, weight)

    def _calculate_priority_weight(self, task: Task) -> float:
        return float(task.priority) / 5.0

    def _calculate_deadline_urgency(self, task: Task) -> float:
        if not task.deadline:
            return 1.0
        try:
            deadline_dt = datetime.fromisoformat(task.deadline)
            now = datetime.now()
            if deadline_dt <= now:
                return 3.0
            days_left = (deadline_dt - now).days
            if days_left <= 1:
                return 2.5
            elif days_left <= 3:
                return 1.5
            elif days_left <= 7:
                return 1.0 + (7.0 - days_left) * 0.1
            else:
                return 0.5
        except:
            return 1.0

    def _calculate_energy_match(self, task: Task, current_energy: str) -> float:
        energy_score = {"low": 0, "medium": 1, "high": 2}
        task_energy = energy_score.get(task.energy_required, 1)
        current_energy_score = energy_score.get(current_energy, 1)
        energy_diff = abs(task_energy - current_energy_score)
        return max(0.5, 1.5 - energy_diff * 0.3)

    def _calculate_resistance_factor(self, task: Task) -> float:
        resistance_penalty = {"low": 1.0, "medium": 0.8, "high": 0.6}
        return resistance_penalty.get(task.resistance, 1.0)

    def _calculate_success_rate_factor(self, task: Task) -> float:
        return 0.5 + task.success_rate * 0.5

    def _calculate_refusal_penalty(self, task: Task) -> float:
        return max(0.3, 1.0 - task.refusal_count * 0.1)

    def _calculate_profile_strategy_weight(self, task: Task) -> float:
        profile = task.task_profile
        now = datetime.now()

        if profile == TaskProfile.DAILY_HABIT.value:
            return 0.0

        elif profile == TaskProfile.WEEKLY_ROUTINE.value:
            weekday = now.weekday()
            if weekday <= 3:
                return 0.3
            elif weekday <= 5:
                return 1.5
            else:
                return 3.0

        elif profile == TaskProfile.DEADLINE_FLEXIBLE.value:
            if not task.deadline:
                return 1.0
            try:
                deadline_dt = datetime.fromisoformat(task.deadline)
                days_left = (deadline_dt - now).days
                if days_left > 7:
                    return 0.5
                elif days_left > 3:
                    return 1.0
                elif days_left > 1:
                    return 1.5
                else:
                    return 2.5
            except:
                return 1.0

        elif profile == TaskProfile.DEADLINE_PROGRESSIVE.value:
            return 1.0

        return 1.0

    def _calculate_cooldown_factor(self, task: Task, session_context: Dict) -> float:
        factor = 1.0

        last_task_id = session_context.get('last_drawn_task_id')
        if last_task_id is not None and task.id == last_task_id:
            return 0.0

        last_category = session_context.get('last_drawn_category')
        if last_category is not None and task.category == last_category:
            factor *= 0.3

        category_count = session_context.get('category_count_in_last_3', {})
        if category_count.get(task.category, 0) >= 2:
            factor *= 0.5

        if task.draw_count_today >= 3:
            factor *= 0.2

        return factor

    def get_tasks_by_profile(self, profile: str) -> List[Task]:
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE task_profile = ? AND completed = 0', (profile,))
        return [Task.from_row(row) for row in cursor.fetchall()]

    def check_and_reset_periodic_tasks(self):
        self.db.reset_daily_tasks()
        self.db.reset_weekly_tasks()
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE tasks SET draw_count_today = 0")
        self.db.conn.commit()

    def get_random_task(self):
        tasks = self.get_all_tasks(include_completed=False)
        if tasks:
            return random.choice(tasks)
        return None

    def set_rest_day(self):
        pass