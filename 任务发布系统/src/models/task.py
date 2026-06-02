from datetime import datetime
from typing import Optional, List
from enum import Enum


class TaskCategory(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    FLEXIBLE_DDL = "flexible_ddl"
    ACCUMULATION = "accumulation"


class RepeatType(Enum):
    NONE = "none"
    SINGLE = "single"
    DAILY = "daily"
    WEEKLY = "weekly"
    ACCUMULATION = "accumulation"


class TaskProfile(Enum):
    DAILY_HABIT = "daily_habit"
    WEEKLY_ROUTINE = "weekly_routine"
    DEADLINE_FLEXIBLE = "deadline_flexible"
    DEADLINE_PROGRESSIVE = "deadline_progressive"


class Resistance(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EnergyRequired(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task:
    def __init__(
        self,
        id: Optional[int] = None,
        name: str = "",
        category: str = TaskCategory.DAILY.value,
        description: Optional[str] = None,
        estimated_time: Optional[int] = None,
        preferred_time: Optional[str] = None,
        deadline: Optional[str] = None,
        resistance: str = Resistance.MEDIUM.value,
        energy_required: str = EnergyRequired.MEDIUM.value,
        rarity: str = "common",
        priority: int = 5,
        success_rate: float = 0.0,
        refusal_count: int = 0,
        is_daily: bool = False,
        task_type: str = "other",
        repeat_type: str = RepeatType.NONE.value,
        task_profile: str = TaskProfile.DEADLINE_FLEXIBLE.value,
        parent_task_id: Optional[int] = None,
        group_id: Optional[str] = None,
        last_completed_at: Optional[str] = None,
        next_available_at: Optional[str] = None,
        last_drawn_at: Optional[str] = None,
        draw_count_today: int = 0,
        min_push_time: str = "20:00",
        in_discard_pile: bool = False,
        completed_count: int = 0,
        tags: List[str] = None,
        completed: bool = False,
        difficulty: Optional[int] = None,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        prerequisite_ids: Optional[List[int]] = None,
        is_unlocked: bool = True
    ):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.estimated_time = estimated_time
        self.preferred_time = preferred_time
        self.deadline = deadline
        self.resistance = resistance
        self.energy_required = energy_required
        self.rarity = rarity
        self.priority = priority
        self.success_rate = success_rate
        self.refusal_count = refusal_count
        self.is_daily = is_daily
        self.task_type = task_type
        self.repeat_type = repeat_type
        self.task_profile = task_profile
        self.parent_task_id = parent_task_id
        self.group_id = group_id
        self.last_completed_at = last_completed_at
        self.next_available_at = next_available_at
        self.last_drawn_at = last_drawn_at
        self.draw_count_today = draw_count_today
        self.min_push_time = min_push_time
        self.in_discard_pile = in_discard_pile
        self.completed_count = completed_count
        self.tags = tags or []
        self.completed = completed
        self.difficulty = difficulty
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.prerequisite_ids = prerequisite_ids or []
        self.is_unlocked = is_unlocked

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "estimated_time": self.estimated_time,
            "preferred_time": self.preferred_time,
            "deadline": self.deadline,
            "resistance": self.resistance,
            "energy_required": self.energy_required,
            "rarity": self.rarity,
            "priority": self.priority,
            "success_rate": self.success_rate,
            "refusal_count": self.refusal_count,
            "is_daily": self.is_daily,
            "task_type": self.task_type,
            "repeat_type": self.repeat_type,
            "task_profile": self.task_profile,
            "parent_task_id": self.parent_task_id,
            "group_id": self.group_id,
            "last_completed_at": self.last_completed_at,
            "next_available_at": self.next_available_at,
            "last_drawn_at": self.last_drawn_at,
            "draw_count_today": self.draw_count_today,
            "min_push_time": self.min_push_time,
            "in_discard_pile": self.in_discard_pile,
            "completed_count": self.completed_count,
            "tags": self.tags,
            "completed": self.completed,
            "difficulty": self.difficulty,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "prerequisite_ids": self.prerequisite_ids,
            "is_unlocked": self.is_unlocked
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            category=data.get("category", TaskCategory.DAILY.value),
            description=data.get("description"),
            estimated_time=data.get("estimated_time"),
            preferred_time=data.get("preferred_time"),
            deadline=data.get("deadline"),
            resistance=data.get("resistance", Resistance.MEDIUM.value),
            energy_required=data.get("energy_required", EnergyRequired.MEDIUM.value),
            rarity=data.get("rarity", "common"),
            priority=data.get("priority", 5),
            success_rate=data.get("success_rate", 0.0),
            refusal_count=data.get("refusal_count", 0),
            is_daily=data.get("is_daily", False),
            task_type=data.get("task_type", "other"),
            repeat_type=data.get("repeat_type", RepeatType.NONE.value),
            task_profile=data.get("task_profile", TaskProfile.DEADLINE_FLEXIBLE.value),
            parent_task_id=data.get("parent_task_id"),
            group_id=data.get("group_id"),
            last_completed_at=data.get("last_completed_at"),
            next_available_at=data.get("next_available_at"),
            last_drawn_at=data.get("last_drawn_at"),
            draw_count_today=data.get("draw_count_today", 0),
            min_push_time=data.get("min_push_time", "20:00"),
            in_discard_pile=data.get("in_discard_pile", False),
            completed_count=data.get("completed_count", 0),
            tags=data.get("tags", []),
            completed=data.get("completed", False),
            difficulty=data.get("difficulty"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            prerequisite_ids=data.get("prerequisite_ids", []),
            is_unlocked=data.get("is_unlocked", True)
        )

    @classmethod
    def from_row(cls, row) -> "Task":
        def safe_get(row, key, default=None):
            try:
                value = row[key]
                return value if value is not None else default
            except (KeyError, IndexError):
                return default

        prereq_raw = safe_get(row, "prerequisite_ids")
        prereq_ids = []
        if prereq_raw:
            import json
            try:
                prereq_ids = json.loads(prereq_raw)
            except:
                pass

        return cls(
            id=safe_get(row, "id"),
            name=safe_get(row, "name", ""),
            category=safe_get(row, "category", "other"),
            description=safe_get(row, "description", ""),
            estimated_time=safe_get(row, "estimated_time", 30),
            preferred_time=safe_get(row, "preferred_time"),
            deadline=safe_get(row, "deadline"),
            resistance=safe_get(row, "resistance", "medium"),
            energy_required=safe_get(row, "energy_required", "medium"),
            rarity=safe_get(row, "rarity", "common"),
            priority=safe_get(row, "priority", 5),
            success_rate=safe_get(row, "success_rate", 0.0),
            refusal_count=safe_get(row, "refusal_count", 0),
            is_daily=bool(safe_get(row, "is_daily", False)),
            task_type=safe_get(row, "task_type", "other"),
            repeat_type=safe_get(row, "repeat_type", RepeatType.NONE.value),
            task_profile=safe_get(row, "task_profile", TaskProfile.DEADLINE_FLEXIBLE.value),
            parent_task_id=safe_get(row, "parent_task_id"),
            group_id=safe_get(row, "group_id"),
            last_completed_at=safe_get(row, "last_completed_at"),
            next_available_at=safe_get(row, "next_available_at"),
            last_drawn_at=safe_get(row, "last_drawn_at"),
            draw_count_today=safe_get(row, "draw_count_today", 0),
            min_push_time=safe_get(row, "min_push_time", "20:00"),
            in_discard_pile=bool(safe_get(row, "in_discard_pile", False)),
            completed_count=safe_get(row, "completed_count", 0),
            tags=safe_get(row, "tags", []),
            completed=bool(safe_get(row, "completed", False)),
            difficulty=safe_get(row, "difficulty"),
            created_at=safe_get(row, "created_at"),
            updated_at=safe_get(row, "updated_at"),
            prerequisite_ids=prereq_ids,
            is_unlocked=bool(safe_get(row, "is_unlocked", True))
        )
