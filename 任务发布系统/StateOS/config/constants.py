"""
StateOS 配置常量
包含所有系统配置和映射规则
"""

from typing import List

# ==================== 状态映射配置 ====================
SLEEP_QUALITY_MAPPING = {
    "神清气爽，精力充沛": {"energy": 90, "thirst": 80, "hunger": 70},
    "基本恢复，状态尚可": {"energy": 75, "thirst": 70, "hunger": 60},
    "略有疲乏，需要启动": {"energy": 60, "thirst": 60, "hunger": 50},
    "没睡好，感到困倦": {"energy": 40, "thirst": 50, "hunger": 40},
    "没睡好，头痛/头晕": {"energy": 30, "thirst": 50, "hunger": 40},
}

# 第二级评估调整规则
SECOND_LEVEL_ADJUSTMENTS = {
    "明显好转，可以开始": 35,
    "略有改善，但需谨慎": 15,
    "没有变化，仍感不适": 0,
}

# 战术指令预设值
TACTICAL_COMMANDS = {
    "紧急补水": {"thirst": 100},
    "强制休息": {"energy": 30},
    "状态超频": {"energy": 100, "high_energy_duration": 90},  # 分钟
    "认知过载": {"effect": "clear_tasks"},
}

# 常规活动规则库
ACTIVITY_RULES = {
    "开始学习(60分钟)": {"energy": -15, "thirst": -10, "hunger": -5},
    "小睡(20分钟)": {"energy": 25, "thirst": -5, "hunger": 0},
    "用餐(一顿)": {"energy": 20, "thirst": -10, "hunger": 80},
    "轻度活动(15分钟)": {"energy": 10, "thirst": -15, "hunger": -5},
    "喝水(一杯)": {"thirst": 30},
    "高强度学习(90分钟)": {"energy": -25, "thirst": -20, "hunger": -10},
}

# 默认课程选项（不再从这里导入，改为硬编码默认值）
DEFAULT_COURSE_OPTIONS = [
    "无安排",
    "高数课",
    "线代课",
    "英语课",
    "编程课",
    "算法课",
    "数据结构课",
    "数据库课",
    "操作系统课",
    "计算机网络课",
    "自习课",
    "阅读时间",
    "项目工作",
    "团队会议",
    "一对一辅导",
    "实验课",
    "运动锻炼",
    "外出办事",
    "休闲娱乐",
    "家庭时间",
    "其他安排"
]

# 时间段配置
TIME_SLOTS = {
    "morning_1": "上午第一时段 (08:00-10:00)",
    "morning_2": "上午第二时段 (10:00-12:00)",
    "afternoon_1": "下午第一时段 (14:00-16:00)",
    "afternoon_2": "下午第二时段 (16:00-18:00)",
    "evening": "晚间时段 (19:00-21:00)"
}

# 时间段对应的精力消耗系数
TIME_SLOT_ENERGY_FACTORS = {
    "morning_1": 1.0,    # 正常消耗
    "morning_2": 1.1,    # 上午后期稍累
    "afternoon_1": 1.2,  # 下午开始容易困
    "afternoon_2": 1.3,  # 下午后期较累
    "evening": 1.5       # 晚上精力较差
}

# 界面颜色配置
UI_COLORS = {
    "补水按钮": "#3498db",      # 蓝色
    "休息按钮": "#e74c3c",      # 红色
    "超频按钮": "#2ecc71",      # 绿色
    "过载按钮": "#f39c12",      # 橙色
    "高能状态": "#f1c40f",      # 黄色
    "低功耗状态": "#95a5a6",    # 灰色
    "正常状态": "#34495e",      # 深蓝灰
    "背景色": "#f5f7fa",        # 浅灰
    "文字色": "#333333",        # 深灰
    "进度条_精力": "#2ecc71",   # 绿色
    "进度条_口渴": "#3498db",   # 蓝色
    "进度条_饥饿": "#e67e22",   # 橙色
}

# 系统参数
SYSTEM_PARAMS = {
    "morning_recalibration_minutes": 30,
    "high_energy_duration_minutes": 90,
    "auto_save_interval_minutes": 5,
    "state_update_interval_seconds": 60,
    "min_state_value": 0,
    "max_state_value": 100,
}

# 状态阈值提醒（默认值，实际从配置文件获取）
THRESHOLD_ALERTS = {
    "energy": {"low": 30, "critical": 15},
    "thirst": {"low": 40, "critical": 20},
    "hunger": {"low": 30, "critical": 15},
}

# 数据库配置
DATABASE_CONFIG = {
    "db_name": "stateos.db",
    "backup_dir": "backups",
    "max_backup_files": 30,
    "backup_interval_hours": 24,
}