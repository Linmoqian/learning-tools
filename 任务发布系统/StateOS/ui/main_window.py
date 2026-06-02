"""
主窗口模块
包含主仪表盘和所有交互元素
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QProgressBar, QSlider, QGroupBox,
    QFrame, QMessageBox, QSpacerItem, QSizePolicy, QMenu, QSystemTrayIcon, QApplication,
    QStyle
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QAction
from typing import Dict, List, Optional, Any, Tuple  # ← 添加这一行
import os
import sys

from core.database import DatabaseManager
from core.state_engine import StateEngine
from config.constants import UI_COLORS
from ui.overload_dialog import OverloadDialog


class MainWindow(QMainWindow):
    """主窗口"""

    state_updated = pyqtSignal(dict)  # 状态更新信号

    def get_all_activities(self) -> Dict[str, Dict]:
        """获取所有活动（默认 + 自定义）"""
        from config.config_manager import get_config_manager

        config_mgr = get_config_manager()
        return config_mgr.get_all_activities()

    def update_time_display(self):
        """更新时间显示"""
        from datetime import datetime

        # 更新时间标签
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.setText(f"🕒 {current_time}")

        # 更新时段信息
        time_slot_info = self.state_engine.get_current_time_slot()

        # 更新当前时段
        if time_slot_info['current_slot']:
            slot = time_slot_info['current_slot']
            self.current_slot_label.setText(
                f"当前: {slot['name']} ({slot['current_hour']:02d}:{slot['current_minute']:02d})"
            )

            # 更新剩余时间
            remaining = time_slot_info['remaining_minutes']
            if remaining > 0:
                hours = remaining // 60
                minutes = remaining % 60
                if hours > 0:
                    self.remaining_time_label.setText(f"剩余: {hours}小时{minutes}分钟")
                else:
                    self.remaining_time_label.setText(f"剩余: {minutes}分钟")

                # 根据剩余时间改变颜色
                if remaining < 15:
                    self.remaining_time_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                elif remaining < 30:
                    self.remaining_time_label.setStyleSheet("color: #f39c12;")
                else:
                    self.remaining_time_label.setStyleSheet("color: #27ae60;")
            else:
                self.remaining_time_label.setText("剩余: 时段结束")
                self.remaining_time_label.setStyleSheet("color: #95a5a6;")
        else:
            self.current_slot_label.setText("当前: 非安排时段")
            self.remaining_time_label.setText("剩余: --")
            self.remaining_time_label.setStyleSheet("color: #7f8c8d;")

        # 更新下一时段
        if time_slot_info['next_slot']:
            next_slot = time_slot_info['next_slot']
            minutes_until = next_slot['minutes_until']
            if minutes_until > 60:
                hours = minutes_until // 60
                mins = minutes_until % 60
                self.next_slot_label.setText(
                    f"下一时段: {next_slot['name']} ({hours}小时后)"
                )
            else:
                self.next_slot_label.setText(
                    f"下一时段: {next_slot['name']} ({minutes_until}分钟后)"
                )
        else:
            self.next_slot_label.setText("下一时段: 今日安排结束")

        # 更新今日安排概要（从数据库获取）
        self.update_schedule_summary()

    def update_schedule_summary(self):
        """更新今日安排概要"""
        try:
            today = self.db.get_today_date()
            checkin = self.db.get_daily_checkin(today)

            if checkin:
                schedule_parts = []
                time_slots = [
                    ('course_morning_1', '早1'),
                    ('course_morning_2', '早2'),
                    ('course_afternoon_1', '下1'),
                    ('course_afternoon_2', '下2'),
                    ('course_evening', '晚')
                ]

                for field, label in time_slots:
                    if field in checkin and checkin[field] and checkin[field] != "无安排":
                        schedule_parts.append(f"{label}:{checkin[field]}")

                if schedule_parts:
                    self.schedule_summary_label.setText(f"今日安排: {' | '.join(schedule_parts)}")
                else:
                    self.schedule_summary_label.setText("今日安排: 无具体安排")
            else:
                self.schedule_summary_label.setText("今日安排: 未设置")

        except Exception as e:
            self.schedule_summary_label.setText("今日安排: 加载失败")

    def apply_time_based_changes(self):
        """应用基于时间的状态变化"""
        # 每分钟触发一次，自动降低状态值
        self.state_engine.calculate_time_based_changes(1)
        self.update_state_display()

    def create_time_slot_display(self) -> QGroupBox:
        """创建时间段显示"""
        group = QGroupBox("🕐 当前时段")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #9b59b6;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 12px;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(10)

        # 当前时段
        self.current_slot_label = QLabel("当前: --")
        self.current_slot_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(self.current_slot_label, 0, 0)

        # 剩余时间
        self.remaining_time_label = QLabel("剩余: --")
        self.remaining_time_label.setFont(QFont("Microsoft YaHei", 11))
        self.remaining_time_label.setStyleSheet("color: #e74c3c;")
        layout.addWidget(self.remaining_time_label, 0, 1)

        # 下一时段
        self.next_slot_label = QLabel("下一时段: --")
        self.next_slot_label.setFont(QFont("Microsoft YaHei", 10))
        self.next_slot_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.next_slot_label, 1, 0, 1, 2)

        # 今日安排概要
        self.schedule_summary_label = QLabel("今日安排: 加载中...")
        self.schedule_summary_label.setFont(QFont("Microsoft YaHei", 9))
        self.schedule_summary_label.setStyleSheet("color: #95a5a6;")
        layout.addWidget(self.schedule_summary_label, 2, 0, 1, 2)

        return group
    def __init__(self, db_manager: DatabaseManager, state_engine: StateEngine):
        super().__init__()
        self.db = db_manager
        self.state_engine = state_engine
        self.setup_ui()
        self.setup_timers()
        self.setup_tray_icon()
        self.load_current_state()

    def setup_ui(self):
        """设置用户界面"""
        self.setWindowTitle("StateOS - 状态操作系统")
        self.setMinimumSize(900, 750)  # 增加高度

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # 减小间距
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 1. 标题栏和时间显示
        header_layout = QHBoxLayout()

        title_label = QLabel("⚡ StateOS - 个人状态管理系统")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {UI_COLORS['正常状态']};")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # 时间显示
        self.time_label = QLabel("")
        self.time_label.setFont(QFont("Microsoft YaHei", 12))
        self.time_label.setStyleSheet("color: #7f8c8d; padding: 5px 15px;")
        header_layout.addWidget(self.time_label)

        main_layout.addLayout(header_layout)

        # 2. 时间段信息
        self.time_slot_group = self.create_time_slot_display()
        main_layout.addWidget(self.time_slot_group)

        # 3. 状态指示器区域
        status_group = self.create_status_indicators()
        main_layout.addWidget(status_group)

        # 3. 战术指令区域
        tactical_group = self.create_tactical_commands()
        main_layout.addWidget(tactical_group)

        # 4. 常规活动区域
        activity_group = self.create_activity_buttons()
        main_layout.addWidget(activity_group)

        # 5. 手动调整区域
        adjustment_group = self.create_adjustment_panel()
        main_layout.addWidget(adjustment_group)

        # 6. 状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        main_layout.addWidget(self.status_label)

        # 添加弹性空间
        main_layout.addStretch()

    def create_status_indicators(self) -> QGroupBox:
        """创建状态指示器"""
        group = QGroupBox("📊 当前状态")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(15)

        # 精力值
        self.energy_label = QLabel("精力值:")
        self.energy_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.energy_label, 0, 0)

        self.energy_bar = QProgressBar()
        self.energy_bar.setRange(0, 100)
        self.energy_bar.setTextVisible(True)
        self.energy_bar.setStyleSheet("""
            QProgressBar {
                height: 25px;
                text-align: center;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: """ + UI_COLORS['进度条_精力'] + """;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.energy_bar, 0, 1)

        self.energy_value = QLabel("75%")
        self.energy_value.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(self.energy_value, 0, 2)

        # 口渴值
        self.thirst_label = QLabel("口渴值:")
        self.thirst_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.thirst_label, 1, 0)

        self.thirst_bar = QProgressBar()
        self.thirst_bar.setRange(0, 100)
        self.thirst_bar.setTextVisible(True)
        self.thirst_bar.setStyleSheet("""
            QProgressBar {
                height: 25px;
                text-align: center;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: """ + UI_COLORS['进度条_口渴'] + """;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.thirst_bar, 1, 1)

        self.thirst_value = QLabel("75%")
        self.thirst_value.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(self.thirst_value, 1, 2)

        # 饥饿值
        self.hunger_label = QLabel("饥饿值:")
        self.hunger_label.setFont(QFont("Microsoft YaHei", 12))
        layout.addWidget(self.hunger_label, 2, 0)

        self.hunger_bar = QProgressBar()
        self.hunger_bar.setRange(0, 100)
        self.hunger_bar.setTextVisible(True)
        self.hunger_bar.setStyleSheet("""
            QProgressBar {
                height: 25px;
                text-align: center;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: """ + UI_COLORS['进度条_饥饿'] + """;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.hunger_bar, 2, 1)

        self.hunger_value = QLabel("75%")
        self.hunger_value.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        layout.addWidget(self.hunger_value, 2, 2)

        # 状态标签区域
        self.status_tags_label = QLabel("")
        self.status_tags_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_tags_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.status_tags_label, 3, 0, 1, 3)

        return group

    def create_tactical_commands(self) -> QGroupBox:
        """创建战术指令按钮"""
        group = QGroupBox("🚀 战术指令")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(15)

        # 紧急补水按钮
        self.hydrate_btn = QPushButton("💧 紧急补水")
        self.hydrate_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_COLORS['补水按钮']};
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
                border-radius: 6px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
            }}
        """)
        self.hydrate_btn.clicked.connect(lambda: self.execute_tactical_command('紧急补水'))
        layout.addWidget(self.hydrate_btn, 0, 0)

        # 强制休息按钮
        self.rest_btn = QPushButton("😴 强制休息")
        self.rest_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_COLORS['休息按钮']};
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
                border-radius: 6px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: #c0392b;
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
            }}
        """)
        self.rest_btn.clicked.connect(lambda: self.execute_tactical_command('强制休息'))
        layout.addWidget(self.rest_btn, 0, 1)

        # 状态超频按钮
        self.overclock_btn = QPushButton("⚡ 状态超频")
        self.overclock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_COLORS['超频按钮']};
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
                border-radius: 6px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: #27ae60;
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
            }}
        """)
        self.overclock_btn.clicked.connect(lambda: self.execute_tactical_command('状态超频'))
        layout.addWidget(self.overclock_btn, 1, 0)

        # 认知过载按钮
        self.overload_btn = QPushButton("🧠 认知过载")
        self.overload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_COLORS['过载按钮']};
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 12px;
                border-radius: 6px;
                min-height: 50px;
            }}
            QPushButton:hover {{
                background-color: #d68910;
            }}
            QPushButton:disabled {{
                background-color: #95a5a6;
            }}
        """)
        self.overload_btn.clicked.connect(self.handle_cognitive_overload)
        layout.addWidget(self.overload_btn, 1, 1)

        return group

    def create_activity_buttons(self) -> QGroupBox:
        """创建常规活动按钮"""
        group = QGroupBox("📝 常规活动")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(10)

        # 获取所有活动
        all_activities = self.get_all_activities()

        if not all_activities:
            no_activities_label = QLabel("暂无活动配置")
            no_activities_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_activities_label)
            return group

        # 创建按钮
        activity_items = list(all_activities.items())

        for i, (activity_name, activity_data) in enumerate(activity_items):
            # 确定显示文本
            display_name = activity_data.get('name', activity_name)
            icon = activity_data.get('icon', '📝')
            display_text = f"{icon} {display_name}"

            btn = QPushButton(display_text)

            # 设置工具提示
            tooltip_parts = []

            # 效果描述
            effects = activity_data.get('effects', {})
            effect_text = []
            if effects.get('energy', 0) != 0:
                change = effects['energy']
                effect_text.append(f"精力: {'+' if change > 0 else ''}{change}")
            if effects.get('thirst', 0) != 0:
                change = effects['thirst']
                effect_text.append(f"口渴: {'+' if change > 0 else ''}{change}")
            if effects.get('hunger', 0) != 0:
                change = effects['hunger']
                effect_text.append(f"饥饿: {'+' if change > 0 else ''}{change}")

            if effect_text:
                tooltip_parts.append("效果: " + ", ".join(effect_text))

            # 持续时间
            duration = activity_data.get('duration')
            if duration:
                tooltip_parts.append(f"持续时间: {duration}分钟")

            # 类型
            activity_type = activity_data.get('type', 'default')
            if activity_type == 'custom':
                tooltip_parts.append("类型: 自定义活动")

            if tooltip_parts:
                btn.setToolTip("\n".join(tooltip_parts))

            # 设置样式
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    padding: 10px 6px;
                    border-radius: 5px;
                    min-height: 40px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
                QPushButton:disabled {
                    background-color: #95a5a6;
                }
            """)

            # 自定义活动使用不同颜色
            if activity_data.get('type') == 'custom':
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #9b59b6;
                        color: white;
                        padding: 10px 6px;
                        border-radius: 5px;
                        min-height: 40px;
                        font-size: 10px;
                        border: 1px solid #8e44ad;
                    }
                    QPushButton:hover {
                        background-color: #8e44ad;
                    }
                """)

            # 连接点击事件
            btn.clicked.connect(lambda checked, an=activity_name: self.execute_activity(an))

            # 计算布局位置（每行4个，因为现在活动可能很多）
            row = i // 4
            col = i % 4
            layout.addWidget(btn, row, col)

        return group

    def execute_activity(self, activity_name: str):
        """执行常规活动"""
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"=== UI执行活动开始: {activity_name} ===")

        all_activities = self.get_all_activities()

        logger.info(f"UI获取到的活动数量: {len(all_activities)}")
        logger.info(f"UI中的活动列表: {list(all_activities.keys())}")

        if activity_name not in all_activities:
            logger.error(f"UI中未找到活动: {activity_name}")
            QMessageBox.warning(self, "活动不存在", f"未找到活动: {activity_name}")
            return

        activity_data = all_activities[activity_name]
        logger.info(f"UI中的活动数据: {activity_data}")
        all_activities = self.get_all_activities()

        if activity_name not in all_activities:
            QMessageBox.warning(self, "活动不存在", f"未找到活动: {activity_name}")
            return

        activity_data = all_activities[activity_name]

        # 获取效果值
        effects = activity_data.get('effects', {})
        energy_change = effects.get('energy', 0)
        thirst_change = effects.get('thirst', 0)
        hunger_change = effects.get('hunger', 0)

        # 获取持续时间
        duration = activity_data.get('duration')

        # 调用状态引擎，传递详细的效果信息
        result = self.state_engine.apply_custom_activity(
            activity_name=activity_name,
            energy_change=energy_change,
            thirst_change=thirst_change,
            hunger_change=hunger_change,
            duration=duration
        )

        if result['success']:
            self.update_state_display()

            # 显示成功消息
            effect_text = []
            for attr, change in result.get('changes', {}).items():
                if change != 0:
                    effect_text.append(f"{attr}: {'+' if change > 0 else ''}{change}")

            if effect_text:
                message = f"✅ 已记录: {activity_name}\n效果: {', '.join(effect_text)}"
            else:
                message = f"✅ 已记录: {activity_name}"

            self.status_label.setText(message)

            # 如果活动有描述，显示通知
            description = activity_data.get('description')
            if description:
                self.show_notification("活动记录", f"{activity_name}: {description}")
        else:
            QMessageBox.warning(self, "活动记录失败", result.get('message', '未知错误'))

    def create_adjustment_panel(self) -> QGroupBox:
        """创建手动调整面板"""
        group = QGroupBox("🎛️ 手动微调")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
            }
        """)

        layout = QGridLayout(group)
        layout.setSpacing(15)

        # 精力值调整
        energy_label = QLabel("精力值调整:")
        energy_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(energy_label, 0, 0)

        self.energy_slider = QSlider(Qt.Orientation.Horizontal)
        self.energy_slider.setRange(0, 100)
        self.energy_slider.setValue(75)
        self.energy_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.energy_slider.setTickInterval(10)
        self.energy_slider.valueChanged.connect(lambda v: self.manual_adjust('energy', v))
        layout.addWidget(self.energy_slider, 0, 1)

        self.energy_slider_value = QLabel("75")
        self.energy_slider_value.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(self.energy_slider_value, 0, 2)

        # 口渴值调整
        thirst_label = QLabel("口渴值调整:")
        thirst_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(thirst_label, 1, 0)

        self.thirst_slider = QSlider(Qt.Orientation.Horizontal)
        self.thirst_slider.setRange(0, 100)
        self.thirst_slider.setValue(75)
        self.thirst_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.thirst_slider.setTickInterval(10)
        self.thirst_slider.valueChanged.connect(lambda v: self.manual_adjust('thirst', v))
        layout.addWidget(self.thirst_slider, 1, 1)

        self.thirst_slider_value = QLabel("75")
        self.thirst_slider_value.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(self.thirst_slider_value, 1, 2)

        # 饥饿值调整
        hunger_label = QLabel("饥饿值调整:")
        hunger_label.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(hunger_label, 2, 0)

        self.hunger_slider = QSlider(Qt.Orientation.Horizontal)
        self.hunger_slider.setRange(0, 100)
        self.hunger_slider.setValue(75)
        self.hunger_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.hunger_slider.setTickInterval(10)
        self.hunger_slider.valueChanged.connect(lambda v: self.manual_adjust('hunger', v))
        layout.addWidget(self.hunger_slider, 2, 1)

        self.hunger_slider_value = QLabel("75")
        self.hunger_slider_value.setFont(QFont("Microsoft YaHei", 11))
        layout.addWidget(self.hunger_slider_value, 2, 2)

        # 连接滑块值显示
        self.energy_slider.valueChanged.connect(lambda v: self.energy_slider_value.setText(str(v)))
        self.thirst_slider.valueChanged.connect(lambda v: self.thirst_slider_value.setText(str(v)))
        self.hunger_slider.valueChanged.connect(lambda v: self.hunger_slider_value.setText(str(v)))

        return group

    def setup_timers(self):
        """设置定时器 - 带自动保存"""
        print("[UI] 设置定时器...")

        try:
            # 状态更新定时器
            self.state_timer = QTimer()
            self.state_timer.timeout.connect(self.update_state_display)
            self.state_timer.start(5000)  # 5秒

            # 时间更新定时器
            self.time_timer = QTimer()
            self.time_timer.timeout.connect(self.update_time_display)
            self.time_timer.start(10000)  # 10秒

            # 自动保存定时器（每2分钟）
            self.auto_save_timer = QTimer()
            self.auto_save_timer.timeout.connect(self.auto_save)
            self.auto_save_timer.start(120000)  # 2分钟

            print("[UI] 定时器设置完成")

        except Exception as e:
            print(f"[UI] 设置定时器失败: {e}")

    def auto_save(self):
        """自动保存状态"""
        try:
            success = self.state_engine.save_current_state()
            if success:
                current_time = self.get_current_time_str()
                self.status_label.setText(f"状态已自动保存 ({current_time})")
                print(f"[UI] 自动保存成功: {current_time}")
        except Exception as e:
            print(f"[UI] 自动保存失败: {e}")

    def get_current_time_str(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M")

    def setup_tray_icon(self):
        """设置系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)

        # 创建托盘菜单
        tray_menu = QMenu()

        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_normal)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 设置图标（使用默认图标）
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        self.tray_icon.show()

        # 托盘图标点击事件
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_normal()

    def load_current_state(self):
        """从数据库加载当前状态"""
        # 状态引擎已经在初始化时加载了状态
        # 这里只需要更新UI显示
        self.update_state_display()

    def update_state_display(self):
        """更新状态显示 - 修复版"""
        try:
            # 获取当前时间戳（确保是数字）
            from datetime import datetime
            current_time = datetime.now().timestamp()  # 返回浮点数

            # 初始化 _last_update 属性
            if not hasattr(self, '_last_update'):
                self._last_update = 0

            # 检查时间间隔（至少间隔2秒）
            time_diff = current_time - self._last_update
            if time_diff < 2.0:  # 至少2秒才更新一次
                return

            self._last_update = current_time

            # 获取状态
            current_state = self.state_engine.get_current_state()

            # 更新UI元素
            self.energy_bar.setValue(current_state['energy'])
            self.energy_value.setText(f"{current_state['energy']}%")

            self.thirst_bar.setValue(current_state['thirst'])
            self.thirst_value.setText(f"{current_state['thirst']}%")

            self.hunger_bar.setValue(current_state['hunger'])
            self.hunger_value.setText(f"{current_state['hunger']}%")

            # 更新滑块
            self.energy_slider.setValue(current_state['energy'])
            self.thirst_slider.setValue(current_state['thirst'])
            self.hunger_slider.setValue(current_state['hunger'])

            # 更新滑块值显示
            self.energy_slider_value.setText(str(current_state['energy']))
            self.thirst_slider_value.setText(str(current_state['thirst']))
            self.hunger_slider_value.setText(str(current_state['hunger']))

            # 更新状态标签
            tags = []
            status_info = self.state_engine.get_status_info()

            if status_info['high_energy_mode']:
                tags.append(f"⚡ 高能状态激活中")
            if status_info['low_power_mode']:
                tags.append(f"🔋 低功耗模式")

            if tags:
                self.status_tags_label.setText(" | ".join(tags))
            else:
                self.status_tags_label.setText("")

            # 更新按钮状态
            self.overclock_btn.setEnabled(not status_info['high_energy_mode'])

            # 检查状态警告
            needs_check = status_info['needs_check']
            warnings = []

            if needs_check.get('energy_low'):
                warnings.append("精力值过低，建议休息")

            if needs_check.get('thirst_low'):
                warnings.append("口渴值过低，建议补水")

            if needs_check.get('hunger_low'):
                warnings.append("饥饿值过低，建议进食")

            if warnings:
                self.status_label.setText("⚠️ " + " | ".join(warnings))
                self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
            else:
                # 偶尔更新统计信息（每5次更新一次）
                if not hasattr(self, '_stat_counter'):
                    self._stat_counter = 0

                self._stat_counter += 1
                if self._stat_counter % 5 == 0:
                    try:
                        stats = self.db.get_today_stats()
                        if stats:
                            stat_text = f"今日: {stats['total_activities']}活动"
                            self.status_label.setText(stat_text)
                            self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")
                    except Exception as e:
                        # 忽略数据库错误，继续运行
                        pass

            # 发出状态更新信号
            if hasattr(self, 'state_updated'):
                self.state_updated.emit(current_state)

        except Exception as e:
            # 更详细的错误信息
            import traceback
            error_msg = f"[UI] 更新状态显示失败: {e}\n{traceback.format_exc()}"
            print(error_msg)

            # 尝试恢复 - 至少更新一次
            try:
                current_state = self.state_engine.get_current_state()
                self.energy_bar.setValue(current_state['energy'])
                self.thirst_bar.setValue(current_state['thirst'])
                self.hunger_bar.setValue(current_state['hunger'])
            except:
                pass

    def get_current_time(self):
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().timestamp()

    def check_state_warnings(self, state: dict, needs_check: dict):
        """检查状态警告"""
        warnings = []

        if needs_check.get('energy_low'):
            warnings.append("精力值过低，建议休息")

        if needs_check.get('thirst_low'):
            warnings.append("口渴值过低，建议补水")

        if needs_check.get('hunger_low'):
            warnings.append("饥饿值过低，建议进食")

        if warnings:
            self.status_label.setText("⚠️ " + " | ".join(warnings))
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")
        else:
            # 显示今日统计
            stats = self.db.get_today_stats()
            if stats:
                stat_text = f"今日: {stats['total_activities']}活动 | {stats['tactical_commands']}战术 | {stats['manual_adjustments']}调整"
                self.status_label.setText(stat_text)
                self.status_label.setStyleSheet("color: #27ae60; padding: 5px;")

    def check_state_reminders(self):
        """检查状态提醒"""
        # 这里可以添加定期提醒逻辑
        pass

    def execute_tactical_command(self, command: str):
        """执行战术指令"""
        result = self.state_engine.apply_tactical_command(command)

        if result['success']:
            QMessageBox.information(self, "执行成功", result['message'])
            self.update_state_display()
            self.show_notification("战术指令", result['message'])
        else:
            QMessageBox.warning(self, "执行失败", result['message'])

    def execute_activity(self, activity_name: str):
        """执行常规活动"""
        all_activities = self.get_all_activities()

        if activity_name not in all_activities:
            QMessageBox.warning(self, "活动不存在", f"未找到活动: {activity_name}")
            return

        activity_data = all_activities[activity_name]
        effects = activity_data.get('effects', {})
        duration = activity_data.get('duration')

        # 直接传递活动名称，不需要添加 custom_ 前缀
        # 状态引擎会从配置中查找对应的效果
        result = self.state_engine.apply_activity(activity_name, duration)

        if result['success']:
            self.update_state_display()

            # 显示成功消息
            effect_text = []
            for attr, change in result.get('changes', {}).items():
                if change != 0:
                    effect_text.append(f"{attr}: {'+' if change > 0 else ''}{change}")

            if effect_text:
                message = f"✅ 已记录: {activity_name}\n效果: {', '.join(effect_text)}"
            else:
                message = f"✅ 已记录: {activity_name}"

            self.status_label.setText(message)

            # 如果活动有描述，显示通知
            description = activity_data.get('description')
            if description:
                self.show_notification("活动记录", f"{activity_name}: {description}")
        else:
            QMessageBox.warning(self, "活动记录失败", result.get('message', '未知错误'))

    def manual_adjust(self, attribute: str, value: int):
        """手动调整状态值"""
        # 只在用户释放滑块时才调整
        if not self.sender().isSliderDown():
            result = self.state_engine.manual_adjust(attribute, value)
            if result['success']:
                self.update_state_display()

    def handle_cognitive_overload(self):
        """处理认知过载"""
        dialog = OverloadDialog(self)
        if dialog.exec():
            # 获取用户输入的任务分解
            tasks = dialog.get_tasks()
            if tasks:
                QMessageBox.information(self, "任务已分解",
                                        f"已将任务分解为 {len(tasks)} 个步骤。\n\n" + "\n".join(
                                            f"• {task}" for task in tasks))
                self.show_notification("认知过载", "任务已成功分解")

    def check_high_energy_mode(self):
        """检查高能状态"""
        result = self.state_engine.check_high_energy_mode()
        if result['ended']:
            QMessageBox.information(self, "高能状态结束", result['message'])
            self.update_state_display()
            self.show_notification("状态更新", result['message'])

    def auto_save(self):
        """自动保存状态"""
        self.state_engine.save_current_state()
        current_time = self.db.get_today_date().split('-')
        time_display = f"{current_time[1]}/{current_time[2]} {self.get_current_time()}"
        self.status_label.setText(f"状态已自动保存 ({time_display})")

    def get_current_time(self):
        """获取当前时间字符串"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M")

    def show_notification(self, title: str, message: str):
        """显示系统通知"""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def show_normal(self):
        """显示窗口"""
        self.show()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event):
        """窗口关闭事件 - 确保保存"""
        print("[UI] 窗口关闭事件")

        try:
            # 保存状态
            print("[UI] 正在保存状态...")
            success = self.state_engine.save_current_state()

            if success:
                print("[UI] 状态保存成功")
            else:
                print("[UI] 状态保存失败")

            # 隐藏窗口，不关闭数据库
            event.ignore()
            self.hide()

            self.show_notification("StateOS", "程序已最小化到系统托盘")

        except Exception as e:
            print(f"[UI] 关闭事件失败: {e}")
            event.ignore()
            self.hide()
