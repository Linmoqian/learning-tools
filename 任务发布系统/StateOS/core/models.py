"""
数据模型定义
定义系统中使用的数据结构和类型
"""

from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, Dict, Any
from enum import Enum


class EventType(Enum):
    """事件类型枚举"""
    MORNING_ASSESSMENT = "morning_assessment"
    MORNING_ADJUSTMENT = "morning_adjustment"
    TACTICAL_COMMAND = "tactical_command"
    REGULAR_ACTIVITY = "regular_activity"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    HIGH_ENERGY_END = "high_energy_end"
    SYSTEM_EVENT = "system_event"


class SleepQuality(Enum):
    """睡眠质量枚举"""
    EXCELLENT = "神清气爽，精力充沛"
    GOOD = "基本恢复，状态尚可"
    TIRED = "略有疲乏，需要启动"
    SLEEPY = "没睡好，感到困倦"
    HEADACHE = "没睡好，头痛/头晕"


class ImprovementLevel(Enum):
    """改善程度枚举"""
    SIGNIFICANT = "明显好转，可以开始"
    SLIGHT = "略有改善，但需谨慎"
    NO_CHANGE = "没有变化，仍感不适"


@dataclass
class DailyCheckin:
    """每日评估记录"""
    id: Optional[int] = None
    date: str = ""
    wake_time: Optional[datetime] = None
    sleep_quality_initial: str = ""
    sleep_quality_adjusted: Optional[str] = None
    course_morning_1: Optional[str] = None
    course_morning_2: Optional[str] = None
    course_afternoon_1: Optional[str] = None
    course_afternoon_2: Optional[str] = None
    course_evening: Optional[str] = None
    energy_initial: Optional[int] = None
    thirst_initial: Optional[int] = None
    hunger_initial: Optional[int] = None
    low_power_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.wake_time:
            result['wake_time'] = self.wake_time.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyCheckin':
        """从字典创建"""
        if 'wake_time' in data and data['wake_time']:
            if isinstance(data['wake_time'], str):
                data['wake_time'] = datetime.fromisoformat(data['wake_time'].replace('Z', '+00:00'))

        return cls(**data)


@dataclass
class StateLog:
    """状态变更日志"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    event_type: str = ""
    event_detail: Optional[str] = None
    energy_before: Optional[int] = None
    energy_after: Optional[int] = None
    thirst_before: Optional[int] = None
    thirst_after: Optional[int] = None
    hunger_before: Optional[int] = None
    hunger_after: Optional[int] = None
    high_energy_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateLog':
        """从字典创建"""
        if 'timestamp' in data and data['timestamp']:
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        return cls(**data)


@dataclass
class DailyState:
    """当日状态"""
    date: str = ""
    current_energy: int = 75
    current_thirst: int = 75
    current_hunger: int = 75
    high_energy_mode: bool = False
    high_energy_end_time: Optional[datetime] = None
    low_power_mode: bool = False
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.high_energy_end_time:
            result['high_energy_end_time'] = self.high_energy_end_time.isoformat()
        if self.last_updated:
            result['last_updated'] = self.last_updated.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DailyState':
        """从字典创建"""
        time_fields = ['high_energy_end_time', 'last_updated']
        for field in time_fields:
            if field in data and data[field]:
                if isinstance(data[field], str):
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))

        return cls(**data)


@dataclass
class ActivityLog:
    """活动记录"""
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    activity_type: str = ""
    duration_minutes: Optional[int] = None
    energy_change: Optional[int] = None
    thirst_change: Optional[int] = None
    hunger_change: Optional[int] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityLog':
        """从字典创建"""
        if 'timestamp' in data and data['timestamp']:
            if isinstance(data['timestamp'], str):
                data['timestamp'] = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))

        return cls(**data)


@dataclass
class UserState:
    """用户当前状态"""
    energy: int = 75
    thirst: int = 75
    hunger: int = 75
    high_energy_mode: bool = False
    low_power_mode: bool = False

    def update(self, **kwargs):
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserState':
        """从字典创建"""
        return cls(**data)


@dataclass
class TacticalCommand:
    """战术指令"""
    name: str
    description: str
    effect: Dict[str, Any]
    color: str
    icon: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ActivityRule:
    """活动规则"""
    name: str
    energy_change: int = 0
    thirst_change: int = 0
    hunger_change: int = 0
    duration_minutes: Optional[int] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class SystemStats:
    """系统统计信息"""
    date: str
    total_activities: int = 0
    tactical_commands: int = 0
    manual_adjustments: int = 0
    morning_assessments: int = 0
    average_energy: Optional[float] = None
    average_thirst: Optional[float] = None
    average_hunger: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
