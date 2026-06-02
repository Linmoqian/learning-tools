"""
计时器管理模块
管理系统中所有的计时器和定时任务
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging


class TimerManager:
    """计时器管理器"""

    def __init__(self):
        self.timers: Dict[str, threading.Timer] = {}
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger(__name__)

    def start(self):
        """启动计时器管理器"""
        if not self.running:
            self.running = True
            self.logger.info("计时器管理器已启动")

    def stop(self):
        """停止计时器管理器"""
        self.running = False
        self.cancel_all_timers()
        self.cancel_all_scheduled_tasks()
        self.logger.info("计时器管理器已停止")

    def create_timer(self, name: str, interval_seconds: float,
                     callback: Callable, *args, **kwargs) -> bool:
        """创建定时器"""
        try:
            # 如果同名计时器已存在，先取消
            if name in self.timers:
                self.cancel_timer(name)

            timer = threading.Timer(interval_seconds, callback, args, kwargs)
            timer.name = name
            self.timers[name] = timer
            timer.start()

            self.logger.info(f"创建计时器: {name}, 间隔: {interval_seconds}秒")
            return True

        except Exception as e:
            self.logger.error(f"创建计时器失败 {name}: {e}")
            return False

    def cancel_timer(self, name: str) -> bool:
        """取消定时器"""
        try:
            if name in self.timers:
                timer = self.timers[name]
                timer.cancel()
                del self.timers[name]
                self.logger.info(f"取消计时器: {name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消计时器失败 {name}: {e}")
            return False

    def cancel_all_timers(self):
        """取消所有定时器"""
        for name in list(self.timers.keys()):
            self.cancel_timer(name)
        self.logger.info("所有计时器已取消")

    def schedule_task(self, name: str, target_time: datetime,
                      callback: Callable, *args, **kwargs) -> bool:
        """安排定时任务"""
        try:
            now = datetime.now()
            if target_time <= now:
                self.logger.warning(f"计划任务时间已过: {name}")
                return False

            # 计算延迟时间（秒）
            delay_seconds = (target_time - now).total_seconds()

            # 创建计时器
            success = self.create_timer(name, delay_seconds, callback, *args, **kwargs)

            if success:
                self.scheduled_tasks[name] = {
                    'target_time': target_time,
                    'callback': callback,
                    'args': args,
                    'kwargs': kwargs
                }
                self.logger.info(f"安排任务: {name}, 执行时间: {target_time}")

            return success

        except Exception as e:
            self.logger.error(f"安排任务失败 {name}: {e}")
            return False

    def cancel_scheduled_task(self, name: str) -> bool:
        """取消定时任务"""
        try:
            # 取消计时器
            timer_cancelled = self.cancel_timer(name)

            # 从计划任务中移除
            if name in self.scheduled_tasks:
                del self.scheduled_tasks[name]

            if timer_cancelled:
                self.logger.info(f"取消计划任务: {name}")
                return True
            return False

        except Exception as e:
            self.logger.error(f"取消计划任务失败 {name}: {e}")
            return False

    def cancel_all_scheduled_tasks(self):
        """取消所有定时任务"""
        for name in list(self.scheduled_tasks.keys()):
            self.cancel_scheduled_task(name)
        self.logger.info("所有计划任务已取消")

    def schedule_daily_task(self, name: str, hour: int, minute: int,
                            callback: Callable, *args, **kwargs) -> bool:
        """安排每日定时任务"""
        try:
            now = datetime.now()
            target_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)

            # 如果今天的时间已过，安排到明天
            if target_time <= now:
                target_time += timedelta(days=1)

            # 安排任务
            success = self.schedule_task(name, target_time, callback, *args, **kwargs)

            if success:
                # 设置每天重复
                def daily_wrapper():
                    try:
                        callback(*args, **kwargs)
                        # 重新安排明天的任务
                        next_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
                        next_time += timedelta(days=1)
                        self.schedule_task(name, next_time, daily_wrapper)
                    except Exception as e:
                        self.logger.error(f"每日任务执行失败 {name}: {e}")

                # 替换原来的任务
                self.scheduled_tasks[name]['callback'] = daily_wrapper

            return success

        except Exception as e:
            self.logger.error(f"安排每日任务失败 {name}: {e}")
            return False

    def get_timer_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取计时器信息"""
        if name in self.timers:
            timer = self.timers[name]
            return {
                'name': name,
                'alive': timer.is_alive(),
                'interval': getattr(timer, 'interval', None)
            }
        return None

    def get_scheduled_task_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取计划任务信息"""
        if name in self.scheduled_tasks:
            task = self.scheduled_tasks[name]
            now = datetime.now()
            target_time = task['target_time']
            seconds_left = (target_time - now).total_seconds()

            return {
                'name': name,
                'target_time': target_time,
                'seconds_left': max(0, seconds_left),
                'has_timer': name in self.timers
            }
        return None

    def get_all_timers(self) -> Dict[str, Dict[str, Any]]:
        """获取所有计时器信息"""
        result = {}
        for name in self.timers.keys():
            result[name] = self.get_timer_info(name)
        return result

    def get_all_scheduled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有计划任务信息"""
        result = {}
        for name in self.scheduled_tasks.keys():
            result[name] = self.get_scheduled_task_info(name)
        return result

    def cleanup(self):
        """清理已完成的计时器"""
        completed = []
        for name, timer in list(self.timers.items()):
            if not timer.is_alive():
                completed.append(name)

        for name in completed:
            if name in self.timers:
                del self.timers[name]

        if completed:
            self.logger.debug(f"清理已完成计时器: {completed}")

    def wait_for_all(self, timeout: Optional[float] = None):
        """等待所有计时器完成"""
        start_time = time.time()

        while self.timers:
            if timeout is not None and (time.time() - start_time) > timeout:
                self.logger.warning("等待计时器超时")
                break

            # 清理已完成的计时器
            self.cleanup()

            # 短暂休眠避免忙等待
            time.sleep(0.1)

        self.logger.info("所有计时器已完成")
