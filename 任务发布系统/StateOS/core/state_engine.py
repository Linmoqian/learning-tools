"""
状态引擎模块
处理所有状态计算、规则应用和状态变更
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
import logging
from .database import DatabaseManager
from config.constants import (
    SLEEP_QUALITY_MAPPING,
    SECOND_LEVEL_ADJUSTMENTS,
    TACTICAL_COMMANDS,
    ACTIVITY_RULES,
    SYSTEM_PARAMS
)


class StateEngine:
    """状态引擎"""


    def calculate_time_based_changes(self, minutes_passed: int = 1):
        """根据时间流逝计算状态变化"""
        if minutes_passed <= 0:
            return

        # 基础消耗（每分钟）
        base_energy_consumption = 0.1  # 每分钟消耗0.1%精力
        base_thirst_consumption = 0.15  # 每分钟消耗0.15%口渴值
        base_hunger_consumption = 0.08  # 每分钟消耗0.08%饥饿值

        # 应用消耗
        energy_change = -base_energy_consumption * minutes_passed
        thirst_change = -base_thirst_consumption * minutes_passed
        hunger_change = -base_hunger_consumption * minutes_passed

        # 根据当前活动调整消耗
        current_time = datetime.now()
        hour = current_time.hour
        if 14 <= hour < 18:  # 下午时段消耗更高
            energy_change *= 1.2
            thirst_change *= 1.3

        # 应用变化
        self.current_state['energy'] = self._clamp_value(
            self.current_state['energy'] + energy_change
        )
        self.current_state['thirst'] = self._clamp_value(
            self.current_state['thirst'] + thirst_change
        )
        self.current_state['hunger'] = self._clamp_value(
            self.current_state['hunger'] + hunger_change
        )

        # 记录时间流逝（可选）
        if minutes_passed >= 5:  # 每5分钟记录一次
            self._log_state_change(
                event_type='time_passage',
                event_detail=f'时间流逝 {minutes_passed} 分钟',
                before={},
                after=self.current_state.copy()
            )

    def get_current_time_slot(self) -> Dict[str, Any]:
        """获取当前时间段信息"""
        from datetime import datetime

        current_time = datetime.now()
        hour = current_time.hour
        minute = current_time.minute

        time_slots = {
            "morning_1": {"name": "上午第一时段", "start": 8, "end": 10},
            "morning_2": {"name": "上午第二时段", "start": 10, "end": 12},
            "afternoon_1": {"name": "下午第一时段", "start": 14, "end": 16},
            "afternoon_2": {"name": "下午第二时段", "start": 16, "end": 18},
            "evening": {"name": "晚间时段", "start": 19, "end": 21}
        }

        current_slot = None
        next_slot = None
        remaining_minutes = 0

        for slot_id, slot_info in time_slots.items():
            if slot_info["start"] <= hour < slot_info["end"]:
                current_slot = {
                    "id": slot_id,
                    "name": slot_info["name"],
                    "start_hour": slot_info["start"],
                    "end_hour": slot_info["end"],
                    "current_hour": hour,
                    "current_minute": minute
                }
                # 计算剩余分钟
                remaining_minutes = (slot_info["end"] - hour) * 60 - minute
                break

        # 查找下一个时段
        future_slots = []
        for slot_id, slot_info in time_slots.items():
            if slot_info["start"] > hour or (slot_info["start"] == hour and minute == 0):
                future_slots.append((slot_info["start"], slot_id, slot_info["name"]))

        if future_slots:
            future_slots.sort()
            next_start, next_id, next_name = future_slots[0]
            next_slot = {
                "id": next_id,
                "name": next_name,
                "start_hour": next_start,
                "minutes_until": (next_start - hour) * 60 - minute
            }

        return {
            "current_slot": current_slot,
            "next_slot": next_slot,
            "remaining_minutes": remaining_minutes,
            "current_time": f"{hour:02d}:{minute:02d}"
        }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.current_state = {
            'energy': 75,
            'thirst': 75,
            'hunger': 75
        }
        self.high_energy_mode = False
        self.low_power_mode = False
        self.high_energy_end_time = None
        self.setup_logging()

        # 尝试从数据库加载上次的状态
        self.load_saved_state()

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)

    def load_saved_state(self):
        """从数据库加载保存的状态"""
        print("[状态引擎] 正在加载保存的状态...")

        try:
            today = self.db.get_today_date()
            print(f"[状态引擎] 加载今天({today})的状态")

            saved_state = self.db.get_current_state(today)
            print(f"[状态引擎] 数据库返回: {saved_state}")

            if saved_state:
                # 确保所有字段都有值
                self.current_state = {
                    'energy': saved_state.get('current_energy', 75),
                    'thirst': saved_state.get('current_thirst', 75),
                    'hunger': saved_state.get('current_hunger', 75)
                }

                self.high_energy_mode = saved_state.get('high_energy_mode', False)
                self.low_power_mode = saved_state.get('low_power_mode', False)
                self.high_energy_end_time = saved_state.get('high_energy_end_time')

                print(f"[状态引擎] 加载成功: {self.current_state}")
                print(f"[状态引擎] 高能模式: {self.high_energy_mode}")
                print(f"[状态引擎] 低功耗模式: {self.low_power_mode}")
                print(f"[状态引擎] 高能结束时间: {self.high_energy_end_time}")
            else:
                print("[状态引擎] 没有找到保存的状态，使用默认值")
                # 使用默认值
                self.current_state = {'energy': 75, 'thirst': 75, 'hunger': 75}
                self.high_energy_mode = False
                self.low_power_mode = False
                self.high_energy_end_time = None

        except Exception as e:
            print(f"[状态引擎] 加载保存状态失败: {e}")
            import traceback
            traceback.print_exc()
            # 失败时使用默认值
            self.current_state = {'energy': 75, 'thirst': 75, 'hunger': 75}
            self.high_energy_mode = False
            self.low_power_mode = False
            self.high_energy_end_time = None

    def set_current_state(self, state: Dict[str, Any]):
        """设置当前状态"""
        # 确保值在合理范围内
        for key, value in state.items():
            if key in self.current_state:
                self.current_state[key] = self._clamp_value(value)

        self.logger.info(f"状态已设置: {self.current_state}")

    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.current_state.copy()

    def apply_morning_assessment(self, sleep_quality: str) -> Dict[str, int]:
        """应用晨间评估结果"""
        if sleep_quality in SLEEP_QUALITY_MAPPING:
            state = SLEEP_QUALITY_MAPPING[sleep_quality].copy()
            old_state = self.get_current_state()

            self.current_state.update(state)

            # 记录状态变更
            self._log_state_change(
                event_type='morning_assessment',
                event_detail=f'晨间评估: {sleep_quality}',
                before=old_state,
                after=self.current_state.copy()
            )

            self.logger.info(f"应用晨间评估: {sleep_quality} -> {state}")
            return state
        else:
            self.logger.warning(f"未知的睡眠质量选项: {sleep_quality}")
            return self.current_state

    def apply_second_level_adjustment(self, adjustment: str) -> Dict[str, Any]:
        """应用第二级评估调整"""
        if adjustment not in SECOND_LEVEL_ADJUSTMENTS:
            self.logger.warning(f"未知的第二级调整选项: {adjustment}")
            return self.current_state

        energy_adjustment = SECOND_LEVEL_ADJUSTMENTS[adjustment]
        old_state = self.get_current_state()

        # 调整精力值
        new_energy = self._clamp_value(self.current_state['energy'] + energy_adjustment)
        self.current_state['energy'] = new_energy

        # 如果没有变化，设置低功耗模式
        if adjustment == "没有变化，仍感不适":
            self.low_power_mode = True
            self.logger.info("已设置全天低功耗模式")

        # 记录状态变更
        self._log_state_change(
            event_type='morning_adjustment',
            event_detail=f'第二级评估: {adjustment}',
            before=old_state,
            after=self.current_state.copy()
        )

        result = {
            'success': True,
            'energy_adjustment': energy_adjustment,
            'new_energy': new_energy,
            'low_power_mode': self.low_power_mode
        }

        self.logger.info(f"应用第二级调整: {adjustment} -> +{energy_adjustment}精力")
        return result

    def apply_tactical_command(self, command: str) -> Dict[str, Any]:
        """应用战术指令"""
        if command not in TACTICAL_COMMANDS:
            result = {'success': False, 'message': f"未知的战术指令: {command}"}
            self.logger.warning(result['message'])
            return result

        command_config = TACTICAL_COMMANDS[command]
        old_state = self.get_current_state()
        result = {'success': True, 'message': '', 'effects': {}}

        try:
            if command == '紧急补水':
                self.current_state['thirst'] = 100
                result['message'] = "已紧急补水，口渴值恢复至100%"
                result['effects'] = {'thirst': 100}

            elif command == '强制休息':
                self.current_state['energy'] = 30
                result['message'] = "已进入低电量模式，建议安排休息或低认知任务"
                result['effects'] = {'energy': 30}

            elif command == '状态超频':
                self.current_state['energy'] = 100
                self.high_energy_mode = True
                duration = command_config.get('high_energy_duration', 90)
                self.high_energy_end_time = datetime.now() + timedelta(minutes=duration)
                result['message'] = f"已激活高能状态，持续{duration}分钟"
                result['effects'] = {
                    'energy': 100,
                    'high_energy_mode': True,
                    'duration_minutes': duration
                }

            elif command == '认知过载':
                # 这个需要UI层处理，这里只记录
                result['message'] = "请将让你感到过载的任务拆解成最小可执行步骤"
                result['effects'] = {'cognitive_overload': True}

            # 记录状态变更
            self._log_state_change(
                event_type='tactical_command',
                event_detail=f'战术指令: {command}',
                before=old_state,
                after=self.current_state.copy(),
                extra_data={'high_energy_mode': self.high_energy_mode}
            )

            self.logger.info(f"执行战术指令: {command}")

        except Exception as e:
            self.logger.error(f"执行战术指令失败: {e}")
            result = {'success': False, 'message': f"执行失败: {str(e)}"}

        return result

    def apply_activity(self, activity_name: str, duration: Optional[int] = None) -> Dict[str, Any]:
        """应用活动效果 - 直接从配置获取"""
        self.logger.info(f"=== 开始应用活动: {activity_name} ===")

        try:
            # 延迟导入以避免循环导入问题
            from config.config_manager import get_config_manager

            # 获取配置管理器
            config_mgr = get_config_manager()

            # 获取所有活动
            all_activities = config_mgr.get_all_activities()

            self.logger.info(f"配置中有 {len(all_activities)} 个活动")
            self.logger.info(f"活动列表: {list(all_activities.keys())}")

            # 检查活动是否存在
            if activity_name not in all_activities:
                # 尝试不同的名称格式
                possible_names = [
                    activity_name,
                    activity_name.replace('(', '').replace(')', ''),
                    activity_name.split('(')[0].strip() if '(' in activity_name else activity_name
                ]

                found = False
                for possible_name in possible_names:
                    if possible_name in all_activities:
                        activity_name = possible_name  # 更新为找到的名称
                        found = True
                        self.logger.info(f"找到活动（修正名称）: {activity_name}")
                        break

                if not found:
                    self.logger.warning(f"未找到活动: {activity_name}")
                    self.logger.warning(f"可用活动: {list(all_activities.keys())}")
                    return {
                        'success': False,
                        'message': f"未找到活动: {activity_name}"
                    }

            # 获取活动数据
            activity_data = all_activities[activity_name]
            self.logger.info(f"活动数据: {activity_data}")

            # 获取效果值
            effects = activity_data.get('effects', {})
            self.logger.info(f"活动效果: {effects}")

            # 如果没有效果值，记录警告
            if not effects or all(v == 0 for v in effects.values()):
                self.logger.warning(f"活动 {activity_name} 的效果值全部为0: {effects}")

            # 应用效果
            return self._apply_activity_effects(activity_name, effects, duration)

        except ImportError as e:
            self.logger.error(f"导入配置管理器失败: {e}")
            return {
                'success': False,
                'message': f"系统配置错误: {str(e)}"
            }
        except Exception as e:
            self.logger.error(f"应用活动失败: {e}", exc_info=True)
            return {
                'success': False,
                'message': f"应用活动失败: {str(e)}"
            }

    def _apply_activity_effects(self, activity_type: str, effects: Dict[str, int],
                                duration: Optional[int] = None) -> Dict[str, Any]:
        """应用活动效果（内部方法）"""
        try:
            changes = {}
            old_state = self.current_state.copy()

            # 应用精力变化
            energy_change = effects.get('energy', 0)
            if energy_change != 0:
                new_energy = self._clamp_value(self.current_state['energy'] + energy_change)
                changes['energy'] = new_energy - self.current_state['energy']
                self.current_state['energy'] = new_energy

            # 应用口渴变化
            thirst_change = effects.get('thirst', 0)
            if thirst_change != 0:
                new_thirst = self._clamp_value(self.current_state['thirst'] + thirst_change)
                changes['thirst'] = new_thirst - self.current_state['thirst']
                self.current_state['thirst'] = new_thirst

            # 应用饥饿变化
            hunger_change = effects.get('hunger', 0)
            if hunger_change != 0:
                new_hunger = self._clamp_value(self.current_state['hunger'] + hunger_change)
                changes['hunger'] = new_hunger - self.current_state['hunger']
                self.current_state['hunger'] = new_hunger

            # 记录活动日志
            if self.db:
                self.db.add_activity_log(
                    activity_type=activity_type,
                    changes=changes,
                    duration=duration
                )

            # 记录状态变更
            self._log_state_change(
                event_type='activity',
                event_detail=f'活动: {activity_type}',
                before=old_state,
                after=self.current_state.copy()
            )

            # 如果有持续时间，可能还需要其他处理
            if duration:
                self.logger.info(f"活动 {activity_type} 持续 {duration} 分钟")

            return {
                'success': True,
                'message': f"已执行活动: {activity_type}",
                'changes': changes
            }

        except Exception as e:
            self.logger.error(f"应用活动效果失败: {e}")
            return {
                'success': False,
                'message': f"应用活动效果失败: {str(e)}"
            }

    def manual_adjust(self, attribute: str, value: int) -> Dict[str, Any]:
        """手动调整状态值"""
        if attribute not in self.current_state:
            self.logger.error(f"未知的状态属性: {attribute}")
            return {'success': False, 'message': f"未知属性: {attribute}"}

        old_state = self.get_current_state()
        old_value = self.current_state[attribute]

        # 边界检查
        new_value = self._clamp_value(value)

        if old_value == new_value:
            return {'success': True, 'message': '值无变化'}

        self.current_state[attribute] = new_value

        # 记录状态变更
        self._log_state_change(
            event_type='manual_adjustment',
            event_detail=f'手动调整: {attribute}',
            before=old_state,
            after=self.current_state.copy()
        )

        self.logger.info(f"手动调整: {attribute} {old_value} -> {new_value}")

        return {
            'success': True,
            'attribute': attribute,
            'old_value': old_value,
            'new_value': new_value
        }


    def check_high_energy_mode(self) -> Dict[str, Any]:
        """检查高能状态是否结束"""
        if self.high_energy_mode and self.high_energy_end_time:
            if datetime.now() >= self.high_energy_end_time:
                self.high_energy_mode = False
                self.high_energy_end_time = None
                self.logger.info("高能状态已结束")

                # 记录状态变更
                self._log_state_change(
                    event_type='high_energy_end',
                    event_detail='高能状态结束',
                    before=self.current_state.copy(),
                    after=self.current_state.copy(),
                    extra_data={'high_energy_mode': False}
                )

                return {
                    'ended': True,
                    'message': '高能状态已结束',
                    'new_energy': self.current_state['energy']
                }

        return {'ended': False}

    def get_status_info(self) -> Dict[str, Any]:
        """获取状态信息"""
        return {
            'current_state': self.current_state.copy(),
            'high_energy_mode': self.high_energy_mode,
            'low_power_mode': self.low_power_mode,
            'high_energy_end_time': self.high_energy_end_time,
            'needs_check': self._check_state_needs_attention()
        }

    def _check_state_needs_attention(self) -> Dict[str, bool]:
        """检查是否需要关注"""
        from config.config_manager import get_config_manager

        config_manager = get_config_manager()
        threshold_alerts = config_manager.user_config.get('threshold_alerts', {
            'energy': {'low': 30, 'critical': 15},
            'thirst': {'low': 40, 'critical': 20},
            'hunger': {'low': 30, 'critical': 15}
        })

        needs = {
            'energy_low': False,
            'thirst_low': False,
            'hunger_low': False
        }

        if self.current_state['energy'] <= threshold_alerts['energy']['low']:
            needs['energy_low'] = True

        if self.current_state['thirst'] <= threshold_alerts['thirst']['low']:
            needs['thirst_low'] = True

        if self.current_state['hunger'] <= threshold_alerts['hunger']['low']:
            needs['hunger_low'] = True

        return needs

    def _clamp_value(self, value: int) -> int:
        """限制值在0-100之间"""
        min_val = SYSTEM_PARAMS.get('min_state_value', 0)
        max_val = SYSTEM_PARAMS.get('max_state_value', 100)
        return max(min_val, min(max_val, value))

    def _log_state_change(self, event_type: str, event_detail: str,
                          before: Dict[str, Any], after: Dict[str, Any],
                          extra_data: Optional[Dict[str, Any]] = None):
        """记录状态变更到日志"""
        try:
            log_data = {
                'event_type': event_type,
                'event_detail': event_detail,
                'energy_before': before.get('energy'),
                'energy_after': after.get('energy'),
                'thirst_before': before.get('thirst'),
                'thirst_after': after.get('thirst'),
                'hunger_before': before.get('hunger'),
                'hunger_after': after.get('hunger'),
                'high_energy_mode': self.high_energy_mode
            }

            if extra_data:
                log_data.update(extra_data)

            self.db.save_state_log(log_data)

        except Exception as e:
            self.logger.error(f"记录状态变更失败: {e}")

    def save_current_state(self):
        """保存当前状态到数据库"""
        print("[状态引擎] 正在保存当前状态...")

        try:
            from datetime import datetime

            state_data = {
                'date': self.db.get_today_date(),
                'current_energy': self.current_state['energy'],
                'current_thirst': self.current_state['thirst'],
                'current_hunger': self.current_state['hunger'],
                'high_energy_mode': self.high_energy_mode,
                'high_energy_end_time': self.high_energy_end_time,
                'low_power_mode': self.low_power_mode
            }

            print(f"[状态引擎] 保存数据: {state_data}")

            success = self.db.save_current_state(state_data)

            if success:
                print("[状态引擎] 状态保存成功")
            else:
                print("[状态引擎] 状态保存失败")

            return success

        except Exception as e:
            print(f"[状态引擎] 保存状态失败: {e}")
            import traceback
            traceback.print_exc()
            return False

