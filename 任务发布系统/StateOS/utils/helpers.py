"""
辅助函数模块
包含各种通用工具函数
"""

import os
import json
import yaml
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import hashlib


def setup_logging(log_name: str, log_level: int = logging.INFO) -> logging.Logger:
    """设置日志记录器"""
    # 创建日志目录
    log_dir = Path.home() / ".stateos" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志文件名
    today = date.today().isoformat()
    log_file = log_dir / f"{log_name}_{today}.log"

    # 配置日志
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)

    # 清除现有处理器
    logger.handlers.clear()

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def load_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """加载配置文件（支持JSON和YAML）"""
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if file_path.suffix.lower() in ['.yml', '.yaml']:
        return yaml.safe_load(content)
    elif file_path.suffix.lower() == '.json':
        return json.loads(content)
    else:
        # 尝试自动检测
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                raise ValueError(f"无法解析配置文件: {file_path}")


def save_config_file(data: Dict[str, Any], file_path: Union[str, Path],
                     format_type: str = 'auto'):
    """保存配置文件"""
    file_path = Path(file_path)

    # 确保目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if format_type == 'auto':
        if file_path.suffix.lower() in ['.yml', '.yaml']:
            format_type = 'yaml'
        elif file_path.suffix.lower() == '.json':
            format_type = 'json'
        else:
            format_type = 'yaml'  # 默认使用YAML

    with open(file_path, 'w', encoding='utf-8') as f:
        if format_type == 'yaml':
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        elif format_type == 'json':
            json.dump(data, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")


def format_timestamp(dt: Optional[datetime] = None,
                     format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间戳"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def parse_timestamp(timestamp_str: str,
                    format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """解析时间戳字符串"""
    return datetime.strptime(timestamp_str, format_str)


def get_time_difference(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """获取时间差的可读格式"""
    if end_time is None:
        end_time = datetime.now()

    delta = end_time - start_time

    if delta.days > 0:
        return f"{delta.days}天前"
    elif delta.seconds >= 3600:
        hours = delta.seconds // 3600
        return f"{hours}小时前"
    elif delta.seconds >= 60:
        minutes = delta.seconds // 60
        return f"{minutes}分钟前"
    else:
        return f"{delta.seconds}秒前"


def clamp_value(value: Union[int, float], min_val: Union[int, float],
                max_val: Union[int, float]) -> Union[int, float]:
    """限制值在最小值和最大值之间"""
    return max(min_val, min(max_val, value))


def calculate_percentage(value: Union[int, float], total: Union[int, float]) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return (value / total) * 100


def interpolate_color(color1: str, color2: str, ratio: float) -> str:
    """在两个颜色之间插值"""
    # 确保比例在0-1之间
    ratio = clamp_value(ratio, 0.0, 1.0)

    # 解析颜色
    r1 = int(color1[1:3], 16)
    g1 = int(color1[3:5], 16)
    b1 = int(color1[5:7], 16)

    r2 = int(color2[1:3], 16)
    g2 = int(color2[3:5], 16)
    b2 = int(color2[5:7], 16)

    # 插值
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)

    return f"#{r:02x}{g:02x}{b:02x}"


def generate_id(length: int = 8) -> str:
    """生成随机ID"""
    import random
    import string

    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def hash_string(text: str, algorithm: str = 'md5') -> str:
    """计算字符串的哈希值"""
    if algorithm == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == 'sha256':
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"不支持的哈希算法: {algorithm}")


def ensure_directory(directory_path: Union[str, Path]) -> Path:
    """确保目录存在，如果不存在则创建"""
    directory_path = Path(directory_path)
    directory_path.mkdir(parents=True, exist_ok=True)
    return directory_path


def get_file_size(file_path: Union[str, Path], unit: str = 'MB') -> float:
    """获取文件大小"""
    file_path = Path(file_path)

    if not file_path.exists():
        return 0.0

    size_bytes = file_path.stat().st_size

    if unit.upper() == 'KB':
        return size_bytes / 1024
    elif unit.upper() == 'MB':
        return size_bytes / (1024 * 1024)
    elif unit.upper() == 'GB':
        return size_bytes / (1024 * 1024 * 1024)
    else:
        return float(size_bytes)


def backup_file(file_path: Union[str, Path], max_backups: int = 5) -> Optional[Path]:
    """备份文件"""
    file_path = Path(file_path)

    if not file_path.exists():
        return None

    # 创建备份目录
    backup_dir = file_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    backup_path = backup_dir / backup_name

    # 复制文件
    import shutil
    shutil.copy2(file_path, backup_path)

    # 清理旧的备份文件
    cleanup_old_backups(backup_dir, max_backups)

    return backup_path


def cleanup_old_backups(backup_dir: Union[str, Path], max_backups: int):
    """清理旧的备份文件"""
    backup_dir = Path(backup_dir)

    if not backup_dir.exists():
        return

    # 获取所有备份文件
    backup_files = list(backup_dir.glob("*_backup_*"))

    if len(backup_files) <= max_backups:
        return

    # 按修改时间排序
    backup_files.sort(key=lambda x: x.stat().st_mtime)

    # 删除最旧的文件
    files_to_delete = backup_files[:-max_backups]
    for file_path in files_to_delete:
        try:
            file_path.unlink()
        except OSError as e:
            logging.warning(f"无法删除备份文件 {file_path}: {e}")


def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分"


def calculate_average(values: List[Union[int, float]]) -> float:
    """计算平均值"""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_trend(current: float, previous: float) -> Dict[str, Any]:
    """计算趋势"""
    if previous == 0:
        return {
            'change': 0.0,
            'percentage': 0.0,
            'direction': 'stable'
        }

    change = current - previous
    percentage = (change / abs(previous)) * 100

    if change > 0:
        direction = 'up'
    elif change < 0:
        direction = 'down'
    else:
        direction = 'stable'

    return {
        'change': change,
        'percentage': abs(percentage),
        'direction': direction
    }


def validate_email(email: str) -> bool:
    """验证邮箱地址"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """验证手机号码"""
    import re
    pattern = r'^1[3-9]\d{9}$'
    return re.match(pattern, phone) is not None


def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    import platform
    import psutil

    info = {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }

    try:
        info['cpu_count'] = psutil.cpu_count()
        info['memory_total'] = psutil.virtual_memory().total
        info['memory_available'] = psutil.virtual_memory().available
        info['disk_usage'] = psutil.disk_usage('/').percent
    except (ImportError, AttributeError):
        pass

    return info


def bytes_to_human_readable(size_bytes: int) -> str:
    """将字节转换为人类可读的格式"""
    if size_bytes == 0:
        return "0B"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1

    return f"{size_bytes:.2f} {units[unit_index]}"
