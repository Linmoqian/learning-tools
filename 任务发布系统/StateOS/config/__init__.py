"""
StateOS 配置模块
"""

__version__ = "1.0.0"
__author__ = "StateOS Team"

from .config_manager import get_config_manager, get_course_options


def get_course_options_list() -> list:
    """获取课程选项列表（兼容性函数）"""
    return get_course_options()