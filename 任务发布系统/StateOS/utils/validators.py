"""
数据验证模块
包含各种数据验证函数
"""

import re
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date


class ValidationError(Exception):
    """验证错误异常"""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


def validate_required(value: Any, field_name: str) -> bool:
    """验证必填字段"""
    if value is None:
        raise ValidationError(f"{field_name} 不能为空", field_name)

    if isinstance(value, str) and not value.strip():
        raise ValidationError(f"{field_name} 不能为空", field_name)

    if isinstance(value, (list, dict, tuple, set)) and len(value) == 0:
        raise ValidationError(f"{field_name} 不能为空", field_name)

    return True


def validate_string(value: Any, field_name: str,
                    min_length: Optional[int] = None,
                    max_length: Optional[int] = None,
                    pattern: Optional[str] = None) -> bool:
    """验证字符串"""
    if value is None:
        return True  # 非必填字段允许为None

    if not isinstance(value, str):
        raise ValidationError(f"{field_name} 必须是字符串", field_name)

    value = value.strip()

    if min_length is not None and len(value) < min_length:
        raise ValidationError(
            f"{field_name} 长度不能少于 {min_length} 个字符",
            field_name
        )

    if max_length is not None and len(value) > max_length:
        raise ValidationError(
            f"{field_name} 长度不能超过 {max_length} 个字符",
            field_name
        )

    if pattern is not None:
        if not re.match(pattern, value):
            raise ValidationError(
                f"{field_name} 格式不正确",
                field_name
            )

    return True


def validate_integer(value: Any, field_name: str,
                     min_value: Optional[int] = None,
                     max_value: Optional[int] = None) -> bool:
    """验证整数"""
    if value is None:
        return True  # 非必填字段允许为None

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} 必须是整数", field_name)

    if min_value is not None and int_value < min_value:
        raise ValidationError(
            f"{field_name} 不能小于 {min_value}",
            field_name
        )

    if max_value is not None and int_value > max_value:
        raise ValidationError(
            f"{field_name} 不能大于 {max_value}",
            field_name
        )

    return True


def validate_float(value: Any, field_name: str,
                   min_value: Optional[float] = None,
                   max_value: Optional[float] = None) -> bool:
    """验证浮点数"""
    if value is None:
        return True  # 非必填字段允许为None

    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} 必须是数字", field_name)

    if min_value is not None and float_value < min_value:
        raise ValidationError(
            f"{field_name} 不能小于 {min_value}",
            field_name
        )

    if max_value is not None and float_value > max_value:
        raise ValidationError(
            f"{field_name} 不能大于 {max_value}",
            field_name
        )

    return True


def validate_boolean(value: Any, field_name: str) -> bool:
    """验证布尔值"""
    if value is None:
        return True  # 非必填字段允许为None

    if not isinstance(value, bool):
        # 尝试转换常见表示形式
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in ['true', '1', 'yes', 'y', 't']:
                return True
            elif value_lower in ['false', '0', 'no', 'n', 'f']:
                return True
            else:
                raise ValidationError(
                    f"{field_name} 必须是布尔值 (true/false)",
                    field_name
                )
        elif isinstance(value, int):
            if value in [0, 1]:
                return True
            else:
                raise ValidationError(
                    f"{field_name} 必须是布尔值 (0/1)",
                    field_name
                )
        else:
            raise ValidationError(f"{field_name} 必须是布尔值", field_name)

    return True


def validate_datetime(value: Any, field_name: str,
                      min_date: Optional[datetime] = None,
                      max_date: Optional[datetime] = None,
                      format_str: Optional[str] = None) -> bool:
    """验证日期时间"""
    if value is None:
        return True  # 非必填字段允许为None

    dt = None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            if format_str:
                dt = datetime.strptime(value, format_str)
            else:
                # 尝试常见格式
                formats = [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d",
                    "%Y/%m/%d %H:%M:%S",
                    "%Y/%m/%d"
                ]

                for fmt in formats:
                    try:
                        dt = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue

                if dt is None:
                    raise ValueError("无法解析日期")
        except ValueError:
            raise ValidationError(
                f"{field_name} 必须是有效的日期时间格式",
                field_name
            )
    else:
        raise ValidationError(
            f"{field_name} 必须是日期时间",
            field_name
        )

    if min_date is not None and dt < min_date:
        raise ValidationError(
            f"{field_name} 不能早于 {min_date}",
            field_name
        )

    if max_date is not None and dt > max_date:
        raise ValidationError(
            f"{field_name} 不能晚于 {max_date}",
            field_name
        )

    return True


def validate_date(value: Any, field_name: str,
                  min_date: Optional[date] = None,
                  max_date: Optional[date] = None) -> bool:
    """验证日期"""
    if value is None:
        return True  # 非必填字段允许为None

    d = None

    if isinstance(value, date):
        d = value
    elif isinstance(value, datetime):
        d = value.date()
    elif isinstance(value, str):
        try:
            # 尝试常见日期格式
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%Y.%m.%d",
                "%d-%m-%Y",
                "%d/%m/%Y",
                "%d.%m.%Y"
            ]

            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    d = dt.date()
                    break
                except ValueError:
                    continue

            if d is None:
                raise ValueError("无法解析日期")
        except ValueError:
            raise ValidationError(
                f"{field_name} 必须是有效的日期格式",
                field_name
            )
    else:
        raise ValidationError(
            f"{field_name} 必须是日期",
            field_name
        )

    if min_date is not None and d < min_date:
        raise ValidationError(
            f"{field_name} 不能早于 {min_date}",
            field_name
        )

    if max_date is not None and d > max_date:
        raise ValidationError(
            f"{field_name} 不能晚于 {max_date}",
            field_name
        )

    return True


def validate_email(value: str, field_name: str) -> bool:
    """验证邮箱地址"""
    if value is None:
        return True  # 非必填字段允许为None

    validate_string(value, field_name)

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, value):
        raise ValidationError(
            f"{field_name} 必须是有效的邮箱地址",
            field_name
        )

    return True


def validate_phone(value: str, field_name: str, country_code: str = '86') -> bool:
    """验证手机号码"""
    if value is None:
        return True  # 非必填字段允许为None

    validate_string(value, field_name)

    # 移除空格和特殊字符
    clean_value = re.sub(r'[\s\-\(\)\+]', '', value)

    # 中国手机号码验证
    if country_code == '86':
        pattern = r'^1[3-9]\d{9}$'
        if not re.match(pattern, clean_value):
            raise ValidationError(
                f"{field_name} 必须是有效的中国大陆手机号码",
                field_name
            )
    else:
        # 通用手机号码验证（最少10位数字）
        pattern = r'^\d{10,15}$'
        if not re.match(pattern, clean_value):
            raise ValidationError(
                f"{field_name} 必须是有效的手机号码",
                field_name
            )

    return True


def validate_url(value: str, field_name: str) -> bool:
    """验证URL"""
    if value is None:
        return True  # 非必填字段允许为None

    validate_string(value, field_name)

    pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    if not re.match(pattern, value):
        raise ValidationError(
            f"{field_name} 必须是有效的URL",
            field_name
        )

    return True


def validate_choice(value: Any, field_name: str,
                    choices: List[Any]) -> bool:
    """验证选择项"""
    if value is None:
        return True  # 非必填字段允许为None

    if value not in choices:
        choices_str = ", ".join(str(c) for c in choices)
        raise ValidationError(
            f"{field_name} 必须是以下选项之一: {choices_str}",
            field_name
        )

    return True


def validate_range(value: Union[int, float], field_name: str,
                   min_value: Optional[Union[int, float]] = None,
                   max_value: Optional[Union[int, float]] = None) -> bool:
    """验证数值范围"""
    if value is None:
        return True  # 非必填字段允许为None

    if min_value is not None and value < min_value:
        raise ValidationError(
            f"{field_name} 不能小于 {min_value}",
            field_name
        )

    if max_value is not None and value > max_value:
        raise ValidationError(
            f"{field_name} 不能大于 {max_value}",
            field_name
        )

    return True


def validate_list(value: Any, field_name: str,
                  min_length: Optional[int] = None,
                  max_length: Optional[int] = None,
                  item_validator: Optional[callable] = None) -> bool:
    """验证列表"""
    if value is None:
        return True  # 非必填字段允许为None

    if not isinstance(value, (list, tuple, set)):
        raise ValidationError(
            f"{field_name} 必须是列表、元组或集合",
            field_name
        )

    value_list = list(value)

    if min_length is not None and len(value_list) < min_length:
        raise ValidationError(
            f"{field_name} 不能少于 {min_length} 个元素",
            field_name
        )

    if max_length is not None and len(value_list) > max_length:
        raise ValidationError(
            f"{field_name} 不能超过 {max_length} 个元素",
            field_name
        )

    if item_validator is not None:
        for i, item in enumerate(value_list):
            try:
                item_validator(item, f"{field_name}[{i}]")
            except ValidationError as e:
                raise ValidationError(
                    f"{field_name} 第{i + 1}个元素无效: {e.message}",
                    field_name
                )

    return True


def validate_dict(value: Any, field_name: str,
                  required_keys: Optional[List[str]] = None,
                  key_validator: Optional[callable] = None,
                  value_validator: Optional[callable] = None) -> bool:
    """验证字典"""
    if value is None:
        return True  # 非必填字段允许为None

    if not isinstance(value, dict):
        raise ValidationError(
            f"{field_name} 必须是字典",
            field_name
        )

    if required_keys is not None:
        for key in required_keys:
            if key not in value:
                raise ValidationError(
                    f"{field_name} 必须包含键 '{key}'",
                    field_name
                )

    if key_validator is not None:
        for key in value.keys():
            try:
                key_validator(key, f"{field_name}.keys")
            except ValidationError as e:
                raise ValidationError(
                    f"{field_name} 键 '{key}' 无效: {e.message}",
                    field_name
                )

    if value_validator is not None:
        for key, val in value.items():
            try:
                value_validator(val, f"{field_name}['{key}']")
            except ValidationError as e:
                raise ValidationError(
                    f"{field_name} 键 '{key}' 的值无效: {e.message}",
                    field_name
                )

    return True


def validate_state_value(value: int, field_name: str) -> bool:
    """验证状态值（0-100之间）"""
    return validate_range(value, field_name, 0, 100)


def validate_sleep_quality(value: str, field_name: str) -> bool:
    """验证睡眠质量选项"""
    valid_options = [
        "神清气爽，精力充沛",
        "基本恢复，状态尚可",
        "略有疲乏，需要启动",
        "没睡好，感到困倦",
        "没睡好，头痛/头晕"
    ]
    return validate_choice(value, field_name, valid_options)


def validate_improvement_level(value: str, field_name: str) -> bool:
    """验证改善程度选项"""
    valid_options = [
        "明显好转，可以开始",
        "略有改善，但需谨慎",
        "没有变化，仍感不适"
    ]
    return validate_choice(value, field_name, valid_options)


def validate_activity_type(value: str, field_name: str) -> bool:
    """验证活动类型"""
    valid_activities = [
        "开始学习(60分钟)",
        "小睡(20分钟)",
        "用餐(一顿)",
        "轻度活动(15分钟)",
        "喝水(一杯)",
        "高强度学习(90分钟)"
    ]
    return validate_choice(value, field_name, valid_activities)


def validate_tactical_command(value: str, field_name: str) -> bool:
    """验证战术指令"""
    valid_commands = [
        "紧急补水",
        "强制休息",
        "状态超频",
        "认知过载"
    ]
    return validate_choice(value, field_name, valid_commands)


def validate_daily_checkin_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证每日评估数据"""
    errors = []

    try:
        validate_required(data.get('date'), 'date')
        validate_date(data.get('date'), 'date')
    except ValidationError as e:
        errors.append(e.message)

    try:
        validate_required(data.get('sleep_quality_initial'), 'sleep_quality_initial')
        validate_sleep_quality(data.get('sleep_quality_initial'), 'sleep_quality_initial')
    except ValidationError as e:
        errors.append(e.message)

    # 可选字段
    if 'sleep_quality_adjusted' in data and data['sleep_quality_adjusted']:
        try:
            validate_improvement_level(data['sleep_quality_adjusted'], 'sleep_quality_adjusted')
        except ValidationError as e:
            errors.append(e.message)

    # 验证新的时间段字段
    time_slot_fields = [
        'course_morning_1',
        'course_morning_2',
        'course_afternoon_1',
        'course_afternoon_2',
        'course_evening'
    ]

    for field in time_slot_fields:
        if field in data and data[field]:
            # 验证课程选项是否有效
            try:
                if data[field] not in COURSE_OPTIONS:
                    errors.append(f"{field} 必须是有效的课程选项")
            except NameError:
                # 如果COURSE_OPTIONS不在作用域内，跳过这个检查
                pass

    if 'energy_initial' in data and data['energy_initial'] is not None:
        try:
            validate_state_value(data['energy_initial'], 'energy_initial')
        except ValidationError as e:
            errors.append(e.message)

    if 'thirst_initial' in data and data['thirst_initial'] is not None:
        try:
            validate_state_value(data['thirst_initial'], 'thirst_initial')
        except ValidationError as e:
            errors.append(e.message)

    if 'hunger_initial' in data and data['hunger_initial'] is not None:
        try:
            validate_state_value(data['hunger_initial'], 'hunger_initial')
        except ValidationError as e:
            errors.append(e.message)

    return len(errors) == 0, errors


def validate_state_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证状态数据"""
    errors = []

    try:
        validate_required(data.get('date'), 'date')
        validate_date(data.get('date'), 'date')
    except ValidationError as e:
        errors.append(e.message)

    if 'current_energy' in data and data['current_energy'] is not None:
        try:
            validate_state_value(data['current_energy'], 'current_energy')
        except ValidationError as e:
            errors.append(e.message)

    if 'current_thirst' in data and data['current_thirst'] is not None:
        try:
            validate_state_value(data['current_thirst'], 'current_thirst')
        except ValidationError as e:
            errors.append(e.message)

    if 'current_hunger' in data and data['current_hunger'] is not None:
        try:
            validate_state_value(data['current_hunger'], 'current_hunger')
        except ValidationError as e:
            errors.append(e.message)

    return len(errors) == 0, errors


def validate_user_config(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """验证用户配置"""
    errors = []

    # 验证课程选项
    if 'course_options' in data:
        try:
            validate_list(data['course_options'], 'course_options', min_length=1)
        except ValidationError as e:
            errors.append(e.message)

    # 验证阈值提醒
    if 'threshold_alerts' in data:
        try:
            validate_dict(data['threshold_alerts'], 'threshold_alerts')

            for state in ['energy', 'thirst', 'hunger']:
                if state in data['threshold_alerts']:
                    thresholds = data['threshold_alerts'][state]
                    validate_dict(thresholds, f'threshold_alerts.{state}')

                    if 'low' in thresholds:
                        validate_state_value(thresholds['low'], f'threshold_alerts.{state}.low')

                    if 'critical' in thresholds:
                        validate_state_value(thresholds['critical'], f'threshold_alerts.{state}.critical')
        except ValidationError as e:
            errors.append(e.message)

    return len(errors) == 0, errors
