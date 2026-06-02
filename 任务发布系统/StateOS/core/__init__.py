"""
StateOS 核心模块
包含数据库、状态引擎、模型等核心功能
"""

__version__ = "1.0.0"
__all__ = ["DatabaseManager", "StateEngine", "models", "timer_manager"]

from .database import DatabaseManager
from .state_engine import StateEngine
