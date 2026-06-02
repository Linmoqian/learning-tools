"""
配置管理器
负责加载和管理用户配置
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# 硬编码默认课程选项，避免循环导入
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


class ConfigManager:
    """配置管理器"""

    def get_all_activities(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活动（全部来自用户配置）"""
        all_activities = {}

        # 获取用户配置中的活动
        user_activities = self.user_config.get('custom_activities', {})

        # 处理两种格式：列表格式（旧）和字典格式（新）
        if isinstance(user_activities, list):
            # 旧格式：列表
            for activity in user_activities:
                name = activity.get('name')
                if name:
                    all_activities[name] = self._normalize_activity(activity)
        elif isinstance(user_activities, dict):
            # 新格式：字典
            for name, activity_data in user_activities.items():
                all_activities[name] = self._normalize_activity(activity_data)
        else:
            # 空或无活动
            pass

        return all_activities

    def _normalize_activity(self, activity: Any) -> Dict[str, Any]:
        """规范化活动数据格式（支持新旧格式）"""
        if isinstance(activity, dict):
            # 提取效果值（支持新旧字段名）
            energy = activity.get('energy', activity.get('energy_change', 0))
            thirst = activity.get('thirst', activity.get('thirst_change', 0))
            hunger = activity.get('hunger', activity.get('hunger_change', 0))

            # 提取持续时间（支持新旧字段名）
            duration = activity.get('duration', activity.get('duration_minutes'))

            return {
                'name': activity.get('name', ''),
                'effects': {
                    'energy': energy,
                    'thirst': thirst,
                    'hunger': hunger
                },
                'type': 'custom',
                'duration': duration,
                'icon': activity.get('icon', '📝'),
                'description': activity.get('description', '')
            }
        return {}
    def force_reload(self) -> bool:
        """强制重新加载配置"""
        self.logger.info("强制重新加载配置文件")
        return self.load_user_config()

    def __init__(self):
        self.user_config_path = Path(__file__).parent / "user_config.yml"
        self.default_config = self.get_default_config()
        self.user_config = {}
        self.setup_logging()
        self.load_user_config()

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'course_options': DEFAULT_COURSE_OPTIONS,
            'hourly_thirst_consumption': {
                '高数课': 12,
                '线代课': 10,
                '英语课': 8,
                '编程课': 15,
                '算法课': 14,
                '数据结构课': 16,
                '数据库课': 12,
                '操作系统课': 15,
                '计算机网络课': 13,
                '自习课': 8,
                '阅读时间': 4,
                '项目工作': 16,
                '团队会议': 6,
                '一对一辅导': 10,
                '实验课': 14,
                '运动锻炼': 20,
                '外出办事': 18,
                '休闲娱乐': 5,
                '家庭时间': 5,
                '其他安排': 8,
                '默认值': 8
            },
            'task_energy_coefficient': {
                '英语四级单词': 1.5,
                '数学作业': 2.0,
                '编程任务': 2.5,
                '论文写作': 3.0,
                '数据分析': 2.8,
                '简单阅读': 0.8,
                '邮件处理': 1.0,
                '会议准备': 1.8,
                '代码调试': 2.2,
                '创意写作': 2.4
            },
            'threshold_alerts': {
                'energy': {'low': 30, 'critical': 15},
                'thirst': {'low': 40, 'critical': 20},
                'hunger': {'low': 30, 'critical': 15}
            },
            'custom_activities': [],
            'system_recommendations': [],
            'ui_customization': {
                'theme': 'light',
                'font_size': 10,
                'language': 'zh_CN'
            }
        }

    def load_user_config(self) -> bool:
        """加载用户配置"""
        try:
            if not self.user_config_path.exists():
                self.logger.warning(f"用户配置文件不存在: {self.user_config_path}")
                # 创建默认配置文件
                self.create_default_config_file()
                self.user_config = self.default_config.copy()
                return True

            self.logger.info(f"正在加载配置文件: {self.user_config_path}")

            with open(self.user_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.debug(f"配置文件内容长度: {len(content)} 字符")

                # 打印文件内容前200字符用于调试
                preview = content[:200] + ("..." if len(content) > 200 else "")
                self.logger.debug(f"配置文件预览:\n{preview}")

                # 动态导入yaml
                try:
                    import yaml
                    loaded_config = yaml.safe_load(content)
                    self.logger.info("使用YAML解析器加载配置")
                except ImportError:
                    self.logger.warning("yaml模块不可用，尝试使用JSON")
                    import json
                    loaded_config = json.loads(content)
                except yaml.YAMLError as e:
                    self.logger.error(f"YAML解析错误: {e}")
                    self.logger.error("尝试使用备选解析方法...")
                    # 尝试修复常见的YAML格式问题
                    try:
                        import yaml
                        # 尝试不同的解析器
                        loader = yaml.SafeLoader
                        loaded_config = yaml.load(content, Loader=loader)
                    except Exception as e2:
                        self.logger.error(f"备选解析也失败: {e2}")
                        loaded_config = None

                if loaded_config is None:
                    self.logger.warning("配置文件为空，使用默认配置")
                    self.user_config = self.default_config.copy()
                else:
                    self.user_config = loaded_config
                    self.logger.info(f"成功加载配置，包含 {len(self.user_config)} 个键")

                    # 详细检查 custom_activities
                    if 'custom_activities' in self.user_config:
                        activities = self.user_config['custom_activities']
                        self.logger.info(f"=== custom_activities 详细检查 ===")
                        self.logger.info(f"类型: {type(activities)}")
                        self.logger.info(f"值: {activities}")

                        if isinstance(activities, list):
                            self.logger.info(f"活动数量: {len(activities)}")
                            for i, act in enumerate(activities):
                                self.logger.info(f"活动[{i}] - 类型: {type(act)}")
                                self.logger.info(f"活动[{i}] - 值: {act}")
                                if isinstance(act, dict):
                                    self.logger.info(f"活动[{i}] - 包含字段: {list(act.keys())}")
                                    self.logger.info(f"活动[{i}] - name字段值: {act.get('name')}")
                        elif isinstance(activities, dict):
                            self.logger.info(f"活动数量: {len(activities)}")
                            for name, act in activities.items():
                                self.logger.info(f"活动[{name}] - 类型: {type(act)}")
                                self.logger.info(f"活动[{name}] - 值: {act}")
                        else:
                            self.logger.warning(f"custom_activities 不是列表或字典，而是: {type(activities)}")

                    # 打印所有配置键用于调试
                    self.logger.info("配置中的所有键:")
                    for key in self.user_config.keys():
                        self.logger.info(f"  - {key}")

            # 合并默认配置（确保所有必要字段都存在）
            self.merge_with_defaults()

            # 记录课程选项
            if 'course_options' in self.user_config:
                courses = self.user_config['course_options']
                self.logger.info(f"加载的课程选项: {len(courses)} 个")
                self.logger.info(f"前5个课程: {courses[:5]}")

            return True

        except Exception as e:
            self.logger.error(f"加载用户配置失败: {e}")
            import traceback
            self.logger.error("详细错误追踪:")
            self.logger.error(traceback.format_exc())
            self.user_config = self.default_config.copy()
            return False

    def merge_with_defaults(self):
        """合并默认配置"""
        for key, default_value in self.default_config.items():
            if key not in self.user_config:
                self.user_config[key] = default_value
            elif isinstance(default_value, dict) and isinstance(self.user_config.get(key), dict):
                # 深度合并字典
                for sub_key, sub_default in default_value.items():
                    if sub_key not in self.user_config[key]:
                        self.user_config[key][sub_key] = sub_default

    def create_default_config_file(self):
        """创建默认配置文件"""
        try:
            # 确保目录存在
            self.user_config_path.parent.mkdir(parents=True, exist_ok=True)

            # 创建默认配置内容
            default_content = """# StateOS 用户自定义配置
# 修改以下值以个性化您的系统，然后重启程序

# 可选日程安排（在晨间评估中使用）
course_options:
  - 无安排
  - 高数课
  - 线代课
  - 英语课
  - 编程实践
  - 算法学习
  - 项目开发
  - 团队会议
  - 健身运动
  - 休闲阅读
  - 外出办事
  - 家庭时间
  - 其他课程

# 每小时水分消耗百分比（根据活动类型）
hourly_thirst_consumption:
  高数课: 12
  线代课: 10
  英语课: 8
  编程实践: 15
  算法学习: 14
  项目开发: 16
  团队会议: 6
  健身运动: 20
  休闲阅读: 4
  外出办事: 18
  家庭时间: 5
  默认值: 8

# 待办事项精力消耗系数
task_energy_coefficient:
  英语四级单词: 1.5
  数学作业: 2.0
  编程任务: 2.5
  论文写作: 3.0
  数据分析: 2.8
  简单阅读: 0.8
  邮件处理: 1.0
  会议准备: 1.8
  代码调试: 2.2
  创意写作: 2.4

# 状态阈值提醒
threshold_alerts:
  energy:
    low: 30
    critical: 15
  thirst:
    low: 40
    critical: 20
  hunger:
    low: 30
    critical: 15

# 自定义活动规则
custom_activities:
  - name: "冥想(15分钟)"
    energy_change: 20
    thirst_change: -5
    hunger_change: 0
  - name: "咖啡时间"
    energy_change: 25
    thirst_change: -15
    hunger_change: -5
  - name: "社交活动"
    energy_change: -10
    thirst_change: -20
    hunger_change: -15
  - name: "散步(30分钟)"
    energy_change: 15
    thirst_change: -10
    hunger_change: -5

# 系统推荐规则
system_recommendations:
  - condition: "energy < 30 and thirst > 80"
    recommendation: "建议先补水，然后短暂休息"
  - condition: "energy > 80 and hunger < 30"
    recommendation: "高能状态，适合进行深度工作"
  - condition: "energy < 20 and hunger < 20"
    recommendation: "需要补充能量和食物，建议暂停工作"
  - condition: "thirst < 20"
    recommendation: "严重缺水，请立即补水"

# 界面自定义
ui_customization:
  theme: "light"
  font_size: 10
  language: "zh_CN"
  show_tray_icon: true
  minimize_to_tray: true
  auto_startup: false
"""

            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                f.write(default_content)

            self.logger.info(f"已创建默认配置文件: {self.user_config_path}")

        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")

    def save_user_config(self) -> bool:
        """保存用户配置"""
        try:
            with open(self.user_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.user_config, f, allow_unicode=True, default_flow_style=False)

            self.logger.info("用户配置保存成功")
            return True

        except Exception as e:
            self.logger.error(f"保存用户配置失败: {e}")
            return False

    def get_course_options(self) -> List[str]:
        """获取课程选项"""
        options = self.user_config.get('course_options', DEFAULT_COURSE_OPTIONS)
        self.logger.debug(f"返回课程选项: {len(options)} 个")
        return options

    def get_thirst_consumption(self, course: str) -> int:
        """获取指定课程的每小时水分消耗"""
        consumption_map = self.user_config.get('hourly_thirst_consumption', {})
        return consumption_map.get(course, consumption_map.get('默认值', 8))

    def get_task_energy_coefficient(self, task: str) -> float:
        """获取任务精力消耗系数"""
        coefficients = self.user_config.get('task_energy_coefficient', {})
        return coefficients.get(task, 1.0)

    def get_threshold_alerts(self, state_type: str) -> Dict[str, int]:
        """获取状态阈值"""
        alerts = self.user_config.get('threshold_alerts', {})
        return alerts.get(state_type, {'low': 30, 'critical': 15})

    def get_custom_activities(self) -> List[Dict[str, Any]]:
        """获取自定义活动"""
        return self.user_config.get('custom_activities', [])

    def get_all_activities(self) -> Dict[str, Dict[str, Any]]:
        """获取所有活动（全部来自用户配置）"""
        self.logger.info("正在获取所有活动...")

        all_activities = {}
        user_activities = self.user_config.get('custom_activities', {})

        self.logger.info(f"用户活动配置类型: {type(user_activities)}")

        # 处理字典格式（新格式）
        if isinstance(user_activities, dict):
            self.logger.info(f"处理字典格式，有 {len(user_activities)} 个活动")
            for activity_key, activity_data in user_activities.items():
                if not isinstance(activity_data, dict):
                    self.logger.warning(f"活动数据不是字典: {activity_data}")
                    continue

                # 获取活动名称
                name = activity_data.get('name', activity_key)

                # 获取效果（支持新旧字段名）
                effects = activity_data.get('effects', {})
                if not effects:
                    # 尝试旧字段名
                    energy = activity_data.get('energy_change', activity_data.get('energy', 0))
                    thirst = activity_data.get('thirst_change', activity_data.get('thirst', 0))
                    hunger = activity_data.get('hunger_change', activity_data.get('hunger', 0))
                    effects = {
                        'energy': energy,
                        'thirst': thirst,
                        'hunger': hunger
                    }

                all_activities[name] = {
                    'name': name,
                    'effects': effects,
                    'type': 'custom',
                    'duration': activity_data.get('duration', activity_data.get('duration_minutes')),
                    'icon': activity_data.get('icon', '📝'),
                    'description': activity_data.get('description', '')
                }
                self.logger.info(f"添加活动: {name}, 效果: {effects}")

        # 处理列表格式（旧格式 - 向后兼容）
        elif isinstance(user_activities, list):
            self.logger.info(f"处理列表格式，有 {len(user_activities)} 个活动")
            for activity in user_activities:
                if not isinstance(activity, dict):
                    continue

                name = activity.get('name')
                if not name:
                    continue

                # 使用旧字段名
                all_activities[name] = {
                    'name': name,
                    'effects': {
                        'energy': activity.get('energy_change', 0),
                        'thirst': activity.get('thirst_change', 0),
                        'hunger': activity.get('hunger_change', 0)
                    },
                    'type': 'custom',
                    'duration': activity.get('duration_minutes'),
                    'icon': activity.get('icon', '📝'),
                    'description': activity.get('description', '')
                }

        self.logger.info(f"总共获取到 {len(all_activities)} 个活动")
        return all_activities

    def get_activity_duration(self, activity_name: str) -> Optional[int]:
        """根据活动名称猜测持续时间"""
        import re
        # 从名称中提取分钟数，例如："学习(60分钟)" -> 60
        match = re.search(r'\((\d+)\s*分钟\)', activity_name)
        if match:
            return int(match.group(1))

        # 默认持续时间映射
        duration_map = {
            '开始学习(60分钟)': 60,
            '小睡(20分钟)': 20,
            '轻度活动(15分钟)': 15,
            '高强度学习(90分钟)': 90,
            '喝水(一杯)': 5,
            '用餐(一顿)': 30
        }

        return duration_map.get(activity_name)

    def get_system_recommendations(self) -> List[Dict[str, str]]:
        """获取系统推荐规则"""
        return self.user_config.get('system_recommendations', [])

    def get_ui_settings(self) -> Dict[str, Any]:
        """获取UI设置"""
        return self.user_config.get('ui_customization', {})

    def update_course_options(self, new_options: List[str]) -> bool:
        """更新课程选项"""
        try:
            self.user_config['course_options'] = new_options
            return self.save_user_config()
        except Exception as e:
            self.logger.error(f"更新课程选项失败: {e}")
            return False

    def add_course_option(self, course: str) -> bool:
        """添加课程选项"""
        try:
            if 'course_options' not in self.user_config:
                self.user_config['course_options'] = DEFAULT_COURSE_OPTIONS.copy()

            if course not in self.user_config['course_options']:
                self.user_config['course_options'].append(course)
                return self.save_user_config()

            return True

        except Exception as e:
            self.logger.error(f"添加课程选项失败: {e}")
            return False

    def reload_config(self) -> bool:
        """重新加载配置"""
        return self.load_user_config()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取配置管理器实例（单例模式）"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_course_options() -> List[str]:
    """获取课程选项（方便函数）"""
    return get_config_manager().get_course_options()