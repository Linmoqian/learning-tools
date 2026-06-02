from typing import List, Optional, Dict, Tuple
from datetime import datetime
import random
from enum import Enum

from ..models.database import Database
from ..models.task import Task, TaskProfile


class GachaPool(Enum):
    FRAGMENT = "fragment"
    TOMATO = "tomato"
    DEEP = "deep"


class GachaSessionContext:
    def __init__(self):
        self.last_drawn_task_id: Optional[int] = None
        self.last_drawn_category: Optional[str] = None
        self.category_history: List[str] = []
        self.replace_count: int = 0
        self.max_replace_count: int = 1
        self.replace_used: bool = False
        self.replaced_task_id: Optional[int] = None
        self.replace_timestamp: Optional[datetime] = None

    def record_draw(self, task: Task):
        self.last_drawn_task_id = task.id
        self.last_drawn_category = task.category
        self.category_history.append(task.category)
        if len(self.category_history) > 3:
            self.category_history.pop(0)

    def can_replace(self) -> bool:
        return not self.replace_used

    def use_replace(self, task_id: int):
        self.replace_used = True
        self.replaced_task_id = task_id
        self.replace_timestamp = datetime.now()

    @property
    def category_count_in_last_3(self) -> Dict[str, int]:
        counts = {}
        for cat in self.category_history:
            counts[cat] = counts.get(cat, 0) + 1
        return counts


class DrawResult:
    def __init__(self, task: Optional[Task], pool: Optional[GachaPool],
                 can_replace: bool = False, is_replacement: bool = False):
        self.task = task
        self.pool = pool
        self.can_replace = can_replace
        self.is_replacement = is_replacement


class DrawChoiceResult:
    def __init__(self, pool: GachaPool, choices: List[Task],
                 slot_index: int = 0, is_urgent: bool = False):
        self.pool = pool
        self.choices = choices
        self.slot_index = slot_index
        self.is_urgent = is_urgent


class GachaService:
    def __init__(self, db: Database):
        self.db = db

    def get_pool_for_time(self, minutes: int) -> Optional[GachaPool]:
        if minutes < 5:
            return None
        if minutes < 15:
            return GachaPool.FRAGMENT
        elif minutes < 45:
            return GachaPool.TOMATO
        else:
            return GachaPool.DEEP

    def get_available_pools(self) -> List[Dict]:
        pools = [
            {
                "id": GachaPool.FRAGMENT.value,
                "name": "碎片卡池",
                "description": "0-15分钟"
            },
            {
                "id": GachaPool.TOMATO.value,
                "name": "番茄卡池",
                "description": "15-45分钟"
            },
            {
                "id": GachaPool.DEEP.value,
                "name": "深度卡池",
                "description": "45分钟以上"
            }
        ]
        return pools

    def draw_single(self, pool: GachaPool, energy: str = "medium",
                    session_context: Optional[GachaSessionContext] = None) -> Optional[DrawResult]:
        if session_context is None:
            session_context = GachaSessionContext()

        time_range = self._get_time_range(pool)
        available_tasks = self.db.get_available_tasks_for_gacha()

        matching_tasks = [
            task for task in available_tasks
            if time_range[0] <= task.get('estimated_time', 0) < time_range[1]
        ]

        if not matching_tasks:
            matching_tasks = available_tasks

        if not matching_tasks:
            return None

        from ..services.task_service import TaskService
        task_service = TaskService(self.db)

        session_dict = {
            'last_drawn_task_id': session_context.last_drawn_task_id,
            'last_drawn_category': session_context.last_drawn_category,
            'category_count_in_last_3': session_context.category_count_in_last_3,
        }

        selected_task = task_service.select_weighted_random_task(energy, session_dict)

        if selected_task is None:
            return None

        session_context.record_draw(selected_task)

        self._update_draw_count(selected_task.id)

        can_replace = session_context.can_replace() and not session_context.replace_used

        return DrawResult(
            task=selected_task,
            pool=pool,
            can_replace=can_replace,
            is_replacement=False
        )

    def draw_single_with_choices(self, pool: GachaPool, energy: str = "medium",
                                  session_context: Optional[GachaSessionContext] = None,
                                  slot_index: int = 0) -> Optional[DrawChoiceResult]:
        if session_context is None:
            session_context = GachaSessionContext()

        time_range = self._get_time_range(pool)
        available_tasks = self.db.get_available_tasks_for_gacha()

        matching_tasks = [
            task for task in available_tasks
            if time_range[0] <= task.get('estimated_time', 0) < time_range[1]
        ]

        if not matching_tasks:
            matching_tasks = available_tasks

        if not matching_tasks:
            return None

        from ..services.task_service import TaskService
        task_service = TaskService(self.db)

        session_dict = {
            'last_drawn_task_id': session_context.last_drawn_task_id,
            'last_drawn_category': session_context.last_drawn_category,
            'category_count_in_last_3': session_context.category_count_in_last_3,
        }

        task_objects = []
        for t in matching_tasks:
            if isinstance(t, dict):
                task_objects.append(Task.from_dict(t))
            else:
                task_objects.append(t)

        choices = task_service.get_top_weighted_tasks(
            task_objects, n=3,
            current_energy=energy,
            session_context=session_dict
        )

        is_urgent = False
        if choices and choices[0].deadline:
            try:
                from datetime import datetime
                deadline_dt = datetime.fromisoformat(choices[0].deadline)
                is_urgent = (deadline_dt - datetime.now()).days <= 1 or deadline_dt <= datetime.now()
            except:
                pass

        if choices:
            chosen = choices[0]
            session_context.record_draw(chosen)
            self._update_draw_count(chosen.id)

        return DrawChoiceResult(
            pool=pool,
            choices=choices,
            slot_index=slot_index,
            is_urgent=is_urgent
        )

    def draw_multi(self, pool: GachaPool, count: int = 5, energy: str = "medium") -> List[DrawResult]:
        session_context = GachaSessionContext()
        results = []

        for i in range(count):
            result = self.draw_single(pool, energy, session_context)
            if result:
                results.append(result)
                if result.task:
                    session_context.record_draw(result.task)
        return results

    def plan_multi_draw(self, total_minutes: int) -> List[Tuple[GachaPool, int]]:
        if total_minutes < 15:
            return []

        if total_minutes < 25:
            fragment_count = total_minutes // 7
            return [(GachaPool.FRAGMENT, max(1, fragment_count))]
        elif total_minutes < 90:
            tomato_count = total_minutes // 25
            return [(GachaPool.TOMATO, max(1, min(tomato_count, 4)))]
        else:
            deep_count = total_minutes // 50
            deep_count = max(1, min(deep_count, 3))
            remaining = total_minutes - deep_count * 50
            plans = [(GachaPool.DEEP, deep_count)]
            if remaining >= 25:
                plans.append((GachaPool.TOMATO, 1))
            elif remaining >= 7:
                plans.append((GachaPool.FRAGMENT, 1))
            return plans

    def draw_multi_planned(self, total_minutes: int, energy: str = "medium") -> List[DrawChoiceResult]:
        plans = self.plan_multi_draw(total_minutes)
        if not plans:
            return []

        session_context = GachaSessionContext()
        all_results = []
        slot = 0

        for pool, count in plans:
            for i in range(count):
                result = self.draw_single_with_choices(pool, energy, session_context, slot)
                if result and result.choices:
                    all_results.append(result)
                    slot += 1

        return all_results

    def replace_card(self, original_task_id: int, reason: str,
                     pool: GachaPool, session_context: GachaSessionContext,
                     energy: str = "medium") -> Optional[DrawResult]:
        session_context.use_replace(original_task_id)

        self._record_rejection(original_task_id, reason)

        result = self.draw_single(pool, energy, session_context)

        if result and result.task and result.task.id == original_task_id:
            result = self.draw_single(pool, energy, session_context)

        if result:
            result.can_replace = False
            result.is_replacement = True

        return result

    def _update_draw_count(self, task_id: int):
        cursor = self.db.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE tasks
            SET draw_count_today = draw_count_today + 1,
                last_drawn_at = ?,
                updated_at = ?
            WHERE id = ?
        ''', (now, now, task_id))
        self.db.conn.commit()

    def _record_rejection(self, task_id: int, reason: str):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO task_rejection_log (task_id, reason, timestamp)
            VALUES (?, ?, ?)
        ''', (task_id, reason, datetime.now().isoformat()))
        self.db.conn.commit()

    def _get_time_range(self, pool: GachaPool) -> Tuple[int, int]:
        if pool == GachaPool.FRAGMENT:
            return (0, 15)
        elif pool == GachaPool.TOMATO:
            return (15, 45)
        else:
            return (45, 999)

    def record_gacha(self, pool: GachaPool, available_time: int, task_id: int):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO gacha_records (timestamp, pool_name, available_time, task_id, accepted)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), pool.value, available_time, task_id, True))
        self.db.conn.commit()

    def record_refusal(self, pool: GachaPool, available_time: int, task_id: int, reason: str):
        cursor = self.db.conn.cursor()
        cursor.execute('''
            INSERT INTO gacha_records (timestamp, pool_name, available_time, task_id, accepted, refusal_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), pool.value, available_time, task_id, False, reason))
        self.db.conn.commit()

    def update_task_on_completion(self, task_id: int):
        self.db.complete_task_with_repeat_logic(task_id)

    def get_gacha_statistics(self) -> Dict:
        cursor = self.db.conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM gacha_records')
        total = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as accepted FROM gacha_records WHERE accepted = 1')
        accepted = cursor.fetchone()['accepted']

        return {
            "total_draws": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "acceptance_rate": accepted / total if total > 0 else 0
        }