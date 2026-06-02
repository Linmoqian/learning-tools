from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QTextEdit, QFrame,
    QScrollArea, QWidget, QInputDialog,
    QMessageBox, QListWidget, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from datetime import date, timedelta
from typing import Dict, List, Optional

from ..models.database import Database


class ScheduleItemWidget(QFrame):
    """单个时段的安排组件"""
    
    def __init__(self, slot_data: tuple, date_str: str, db: Database, parent=None):
        super().__init__(parent)
        self.slot_id, self.slot_name, self.start_time, self.end_time, self.display_order = slot_data
        self.date_str = date_str
        self.db = db
        self.current_activity = "无安排"
        self.current_notes = ""
        self.current_schedule_type = "temporary"
        self._init_ui()
    
    def _init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f4f8;
                border: 2px solid #d1dce6;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 时段标题
        header_layout = QHBoxLayout()
        title_label = QLabel(f"📅 {self.slot_name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        time_label = QLabel(f"{self.start_time} - {self.end_time}")
        time_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(time_label)
        layout.addLayout(header_layout)
        
        # 日程类型选择
        type_layout = QHBoxLayout()
        type_label = QLabel("类型：")
        type_label.setStyleSheet("font-size: 14px; color: #34495e;")
        type_layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["仅当天 (临时)", "每周固定"])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #d1dce6;
                border-radius: 8px;
                padding: 6px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 2px solid #4A90E2;
            }
        """)
        self.type_combo.setFocusPolicy(Qt.NoFocus)
        self.type_combo.wheelEvent = lambda event: None
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 活动选择
        activity_label = QLabel("安排：")
        activity_label.setStyleSheet("font-size: 14px; color: #34495e;")
        layout.addWidget(activity_label)
        
        self.activity_combo = QComboBox()
        self.activity_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #d1dce6;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
            }
            QComboBox:hover {
                border: 2px solid #4A90E2;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #4A90E2;
            }
        """)
        self.activity_combo.setFocusPolicy(Qt.NoFocus)
        self.activity_combo.wheelEvent = lambda event: None
        self._refresh_activities()
        self.activity_combo.setCurrentText("无安排")
        self.activity_combo.currentTextChanged.connect(self._on_activity_changed)
        layout.addWidget(self.activity_combo)
        
        # 备注
        notes_label = QLabel("备注：")
        notes_label.setStyleSheet("font-size: 14px; color: #34495e;")
        layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("添加备注（可选）")
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #d1dce6;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 2px solid #4A90E2;
            }
        """)
        self.notes_edit.textChanged.connect(self._save_notes)
        layout.addWidget(self.notes_edit)
    
    def _refresh_activities(self):
        """刷新活动选项列表"""
        self.activity_combo.blockSignals(True)
        self.activity_combo.clear()
        activities = self.db.get_activity_options()
        self.activity_combo.addItems(activities)
        self.activity_combo.blockSignals(False)
    
    def set_data(self, activity: Optional[str], notes: Optional[str], schedule_type: str = "temporary"):
        """设置数据"""
        self._refresh_activities()
        self.current_activity = activity or "无安排"
        self.current_notes = notes or ""
        self.current_schedule_type = schedule_type
        
        self.type_combo.blockSignals(True)
        self.type_combo.setCurrentIndex(0 if schedule_type == "temporary" else 1)
        self.type_combo.blockSignals(False)
        
        self.activity_combo.setCurrentText(self.current_activity)
        self.notes_edit.setPlainText(self.current_notes)
        self._update_style(self.current_activity, self.current_schedule_type)
    
    def _on_type_changed(self, index: int):
        """日程类型变化时保存"""
        self.current_schedule_type = "temporary" if index == 0 else "weekly"
        self._save_activity()
        self._update_style(self.current_activity, self.current_schedule_type)
    
    def _on_activity_changed(self, activity: str):
        """活动变化时保存"""
        self.current_activity = activity
        self._save_activity()
        self._update_style(self.current_activity, self.current_schedule_type)
    
    def _save_activity(self):
        """保存活动到数据库"""
        d = date.fromisoformat(self.date_str)
        day_of_week = d.weekday()
        self.db.save_schedule_item(
            self.date_str, self.slot_id, self.current_activity,
            self.current_notes, self.current_schedule_type, day_of_week
        )
    
    def _save_notes(self):
        """保存备注"""
        self.current_notes = self.notes_edit.toPlainText()
        self._save_activity()
    
    def _update_style(self, activity: str, schedule_type: str):
        """根据活动和类型更新样式"""
        if schedule_type == "weekly":
            # 每周固定：蓝色边框
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f4ff;
                    border: 2px solid #4A90E2;
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
        elif activity != "无安排":
            # 临时有安排：浅绿边框
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f4f8;
                    border: 2px solid #4A90E2;
                    border-radius: 12px;
                    padding: 15px;
                }
            """)
        else:
            # 无安排：默认样式
            self.setStyleSheet("""
                QFrame {
                    background-color: #f0f4f8;
                    border: 2px solid #d1dce6;
                    border-radius: 12px;
                    padding: 15px;
                }
            """)


class ActivityManagerDialog(QDialog):
    """活动选项管理对话框"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("管理活动选项")
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("活动选项列表")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 列表
        self.activity_list = QListWidget()
        self.activity_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 2px solid #d1dce6;
                border-radius: 8px;
                padding: 5px;
                font-size: 14px;
                color: #2c3e50;
            }
        """)
        self._refresh_list()
        layout.addWidget(self.activity_list)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ 添加新活动")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: 2px solid #3a7bc8;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        add_btn.clicked.connect(self._add_activity)
        btn_layout.addWidget(add_btn)
        
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #c0392b;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        delete_btn.clicked.connect(self._delete_activity)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("✓ 关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: 2px solid #229954;
                border-radius: 8px;
                padding: 10px 30px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def _refresh_list(self):
        """刷新列表"""
        self.activity_list.clear()
        activities = self.db.get_activity_options()
        for activity in activities:
            item = QListWidgetItem(activity)
            self.activity_list.addItem(item)
    
    def _add_activity(self):
        """添加新活动"""
        name, ok = QInputDialog.getText(
            self,
            "添加活动",
            "请输入新活动的名称："
        )
        if ok and name.strip():
            if self.db.add_activity_option(name.strip()):
                QMessageBox.information(self, "成功", f"活动「{name}」添加成功！")
                self._refresh_list()
            else:
                QMessageBox.warning(self, "失败", f"活动「{name}」已存在！")
    
    def _delete_activity(self):
        """删除活动"""
        current_item = self.activity_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要删除的活动！")
            return
        
        activity_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除活动「{activity_name}」吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.db.delete_activity_option(activity_name):
                QMessageBox.information(self, "成功", f"活动「{activity_name}」删除成功！")
                self._refresh_list()
            else:
                QMessageBox.warning(self, "失败", f"活动「{activity_name}」删除失败！")


class ScheduleWindow(QDialog):
    """课程表管理窗口"""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_date = date.today().isoformat()
        self.slot_widgets: Dict[str, ScheduleItemWidget] = {}
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("📅 日程安排")
        self.setMinimumSize(850, 900)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题和管理按钮
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📅 日程安排")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        manage_btn = QPushButton("⚙️ 管理活动选项")
        manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: 2px solid #8e44ad;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        manage_btn.clicked.connect(self._open_activity_manager)
        header_layout.addWidget(manage_btn)
        
        main_layout.addLayout(header_layout)
        
        # 类型说明
        hint_layout = QHBoxLayout()
        hint1 = QLabel("🔵 每周固定")
        hint1.setStyleSheet("color: #4A90E2; font-weight: bold;")
        hint2 = QLabel("⚪ 仅当天")
        hint2.setStyleSheet("color: #7f8c8d; font-weight: bold;")
        hint_layout.addWidget(hint1)
        hint_layout.addWidget(hint2)
        hint_layout.addStretch()
        main_layout.addLayout(hint_layout)
        
        # 日期选择
        date_layout = QHBoxLayout()
        date_layout.setSpacing(10)
        
        prev_btn = QPushButton("⬅️ 前一天")
        prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: 2px solid #3a7bc8;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        prev_btn.clicked.connect(self._prev_day)
        date_layout.addWidget(prev_btn)
        
        self.date_label = QLabel(self._format_date(self.current_date))
        self.date_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        self.date_label.setAlignment(Qt.AlignCenter)
        date_layout.addWidget(self.date_label)
        
        next_btn = QPushButton("后一天 ➡️")
        next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: 2px solid #3a7bc8;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a7bc8;
            }
        """)
        next_btn.clicked.connect(self._next_day)
        date_layout.addWidget(next_btn)
        
        main_layout.addLayout(date_layout)
        
        # 今日安排概要
        self.summary_label = QLabel("今日安排：加载中...")
        self.summary_label.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        self.summary_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.summary_label)
        
        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: #d1dce6;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #4A90E2;
                border-radius: 5px;
            }
        """)
        
        scroll_content = QWidget()
        self.slots_layout = QVBoxLayout(scroll_content)
        self.slots_layout.setSpacing(12)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 关闭按钮
        close_layout = QHBoxLayout()
        close_layout.addStretch()
        
        close_btn = QPushButton("✓ 关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: 2px solid #229954;
                border-radius: 10px;
                padding: 12px 40px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        close_btn.clicked.connect(self.accept)
        close_layout.addWidget(close_btn)
        close_layout.addStretch()
        main_layout.addLayout(close_layout)
        
        # 加载数据
        self._load_slots()
        self._load_schedule()
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期显示"""
        d = date.fromisoformat(date_str)
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][d.weekday()]
        return f"{d.year}年{d.month}月{d.day}日 ({weekday})"
    
    def _prev_day(self):
        """前一天"""
        d = date.fromisoformat(self.current_date)
        d = d - timedelta(days=1)
        self.current_date = d.isoformat()
        self._update_display()
    
    def _next_day(self):
        """后一天"""
        d = date.fromisoformat(self.current_date)
        d = d + timedelta(days=1)
        self.current_date = d.isoformat()
        self._update_display()
    
    def _update_display(self):
        """更新显示"""
        self.date_label.setText(self._format_date(self.current_date))
        self._load_schedule()
    
    def _load_slots(self):
        """加载所有时段"""
        slots = self.db.get_schedule_slots()
        for slot_data in slots:
            slot_widget = ScheduleItemWidget(slot_data, self.current_date, self.db)
            self.slot_widgets[slot_data[0]] = slot_widget
            self.slots_layout.addWidget(slot_widget)
        
        self.slots_layout.addStretch()
    
    def _load_schedule(self):
        """加载某日的安排"""
        schedule = self.db.get_daily_schedule(self.current_date)
        for item in schedule:
            slot_id, _, _, _, activity, notes, schedule_type, _ = item
            if slot_id in self.slot_widgets:
                widget = self.slot_widgets[slot_id]
                widget.date_str = self.current_date
                widget.set_data(activity, notes, schedule_type)
        
        self._update_summary(schedule)
    
    def _update_summary(self, schedule: list):
        """更新今日安排概要"""
        parts = []
        slot_labels = {
            "morning_1": "早1",
            "morning_2": "早2",
            "afternoon_1": "下1",
            "afternoon_2": "下2",
            "evening": "晚"
        }
        
        for item in schedule:
            slot_id, _, _, _, activity, _, schedule_type, _ = item
            if activity and activity != "无安排":
                label = slot_labels.get(slot_id, slot_id)
                prefix = "🔵" if schedule_type == "weekly" else ""
                parts.append(f"{prefix}{label}:{activity}")
        
        if parts:
            self.summary_label.setText(f"今日安排：{' | '.join(parts)}")
        else:
            self.summary_label.setText("今日安排：无具体安排")
    
    def _open_activity_manager(self):
        """打开活动管理"""
        dialog = ActivityManagerDialog(self.db, self)
        if dialog.exec():
            # 刷新所有卡片的活动列表
            for widget in self.slot_widgets.values():
                widget._refresh_activities()
                widget.set_data(widget.current_activity, widget.current_notes, widget.current_schedule_type)

