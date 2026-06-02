from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QComboBox, QLineEdit, QTextEdit, 
    QSpinBox, QDialog, QFormLayout, QFrame, QScrollArea,
    QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ..models.database import Database
from ..models.task import Task, TaskCategory, Resistance, EnergyRequired, TaskProfile
from ..services.task_service import TaskService
from ..services.state_service import StateService, DailyTone
from ..services.export_service import ExportService
from ..services.ai_import_processor import AIImportProcessor
from .gacha_window import GachaWindow
from .schedule_window import ScheduleWindow
from .dependency_graph import DependencyGraphDialog


MODERN_STYLE = """
QMainWindow {
    background-color: #f8f9fa;
}

QPushButton {
    background-color: #4A90E2;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: bold;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #357ABD;
}

QPushButton:pressed {
    background-color: #2D6AA0;
}

QPushButton:disabled {
    background-color: #CCCCCC;
}

QLabel#TitleLabel {
    color: #2C3E50;
    font-size: 28px;
    font-weight: bold;
}

QLabel#TimerLabel {
    color: #4A90E2;
    font-size: 48px;
    font-weight: bold;
}

QLabel#TaskLabel {
    color: #34495E;
    font-size: 16px;
}

QListWidget {
    background-color: white;
    border: 2px solid #E0E0E0;
    border-radius: 10px;
    padding: 8px;
    font-size: 14px;
}

QListWidget::item {
    background-color: white;
    border-radius: 8px;
    padding: 10px;
    margin: 4px 0px;
}

QTagLabel {
    background-color: #E3F2FD;
    color: #1976D2;
    border-radius: 12px;
    padding: 4px 8px;
    font-size: 12px;
}
"""


class TaskEditDialog(QDialog):
    def __init__(self, parent=None, task=None, db=None):
        super().__init__(parent)
        self.task = task
        self.db = db or Database()
        self._init_ui()
        self._load_prerequisite_tasks()

    def _init_ui(self):
        title = "✏️ 编辑任务" if self.task else "➕ 添加新任务"
        self.setWindowTitle(title)
        self.resize(500, 800)
        self.setStyleSheet(MODERN_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QFormLayout(scroll_content)

        # 任务名称
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("例如：复习高数第七章")
        if self.task:
            self.name_input.setText(self.task.name)
        scroll_layout.addRow("<b>📝 任务名称</b>", self.name_input)

        # 任务类型
        self.task_type_combo = QComboBox()
        task_types = [
            ("normal", "📋 普通任务"),
            ("daily", "🔄 每日习惯"),
            ("weekly", "📅 每周任务"),
            ("deadline", "⏰ 截止日任务"),
            ("accumulation", "📚 积累型任务")
        ]
        for value, display in task_types:
            self.task_type_combo.addItem(display, value)
        if self.task:
            idx = self.task_type_combo.findData(self.task.task_type)
            if idx >= 0:
                self.task_type_combo.setCurrentIndex(idx)
        scroll_layout.addRow("<b>🏷️ 任务类型</b>", self.task_type_combo)

        # 是否每日习惯
        self.is_daily_check = QCheckBox("标记为每日习惯（每天都要做的）")
        if self.task and hasattr(self.task, 'is_daily') and self.task.is_daily:
            self.is_daily_check.setChecked(True)
        scroll_layout.addRow("", self.is_daily_check)

        # 标签
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("标签，用逗号分隔，例如：高数, 复习, 重要")
        if self.task and hasattr(self.task, 'tags') and self.task.tags:
            self.tags_input.setText(", ".join(self.task.tags))
        scroll_layout.addRow("<b>🏷️ 标签</b>", self.tags_input)

        # 描述
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setPlaceholderText("任务描述（可选，例如：重点看积分部分）...")
        if self.task and self.task.description:
            self.desc_input.setText(self.task.description)
        scroll_layout.addRow("<b>📄 描述</b>", self.desc_input)

        # 预计时间
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 480)
        self.time_input.setValue(25)
        self.time_input.setSuffix(" 分钟")
        if self.task and self.task.estimated_time:
            self.time_input.setValue(self.task.estimated_time)
        scroll_layout.addRow("<b>⏱️ 预计时间</b>", self.time_input)

        # 截止日期（可选）
        self.deadline_input = QLineEdit()
        self.deadline_input.setPlaceholderText("YYYY-MM-DD（可选，例如：2024-06-30）")
        if self.task and hasattr(self.task, 'deadline') and self.task.deadline:
            self.deadline_input.setText(self.task.deadline)
        scroll_layout.addRow("<b>📅 截止日期</b>", self.deadline_input)

        # 优先级
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        self.priority_spin.setSuffix(" / 10")
        if self.task and hasattr(self.task, 'priority') and self.task.priority:
            self.priority_spin.setValue(self.task.priority)
        scroll_layout.addRow("<b>⭐ 优先级</b>", self.priority_spin)

        # 阻力
        self.resistance_combo = QComboBox()
        resistances = [
            ("low", "🟢 低阻力（容易开始）"),
            ("medium", "🟡 中阻力（需要一点动力）"),
            ("high", "🔴 高阻力（很难开始）")
        ]
        for value, display in resistances:
            self.resistance_combo.addItem(display, value)
        if self.task:
            idx = self.resistance_combo.findData(self.task.resistance)
            if idx >= 0:
                self.resistance_combo.setCurrentIndex(idx)
        scroll_layout.addRow("<b>💪 心理阻力</b>", self.resistance_combo)

        # 所需精力
        self.energy_combo = QComboBox()
        energies = [
            ("low", "🔋 低精力（可以摸鱼）"),
            ("medium", "🔋🔋 中精力（正常状态）"),
            ("high", "🔋🔋🔋 高精力（需要全神贯注）")
        ]
        for value, display in energies:
            self.energy_combo.addItem(display, value)
        if self.task:
            idx = self.energy_combo.findData(self.task.energy_required)
            if idx >= 0:
                self.energy_combo.setCurrentIndex(idx)
        scroll_layout.addRow("<b>⚡ 所需精力</b>", self.energy_combo)

        # 前置任务选择区
        prereq_label = QLabel("<b>🔗 前置任务（可选）</b>")
        scroll_layout.addRow(prereq_label)

        prereq_info = QLabel("选择需要先完成的任务，设置后可形成依赖链")
        prereq_info.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        scroll_layout.addRow("", prereq_info)

        prereq_search_layout = QHBoxLayout()
        self.prereq_search_input = QLineEdit()
        self.prereq_search_input.setPlaceholderText("搜索任务...")
        self.prereq_search_input.textChanged.connect(self._filter_prerequisite_tasks)
        prereq_search_layout.addWidget(self.prereq_search_input)

        self.prereq_tag_filter = QComboBox()
        self.prereq_tag_filter.addItem("全部标签", "")
        for tag in self.db.get_all_tags():
            self.prereq_tag_filter.addItem(tag, tag)
        self.prereq_tag_filter.currentIndexChanged.connect(self._filter_prerequisite_tasks)
        prereq_search_layout.addWidget(self.prereq_tag_filter)
        scroll_layout.addRow("", prereq_search_layout)

        self.prereq_list = QListWidget()
        self.prereq_list.setSelectionMode(QListWidget.MultiSelection)
        self.prereq_list.setMaximumHeight(150)
        self.prereq_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #d1dce6;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px 8px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }
        """)
        scroll_layout.addRow("", self.prereq_list)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # 按钮
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("✗ 取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        ok_btn = QPushButton("✓ 保存")
        ok_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        main_layout.addLayout(btn_layout)

    def _load_prerequisite_tasks(self):
        self.prereq_list.clear()
        all_tasks = self.db.conn.execute(
            "SELECT id, name, tags FROM tasks WHERE completed = 0 ORDER BY id"
        ).fetchall()

        selected_ids = set()
        if self.task and hasattr(self.task, 'prerequisite_ids') and self.task.prerequisite_ids:
            selected_ids = set(self.task.prerequisite_ids)

        self._prereq_task_items = []
        for row in all_tasks:
            task_dict = dict(row)
            task_id = task_dict['id']
            task_name = task_dict['name']
            task_tags = self.db.get_task_tags(task_id)

            if self.task and task_id == self.task.id:
                continue

            display_text = f"#{task_id} {task_name}"
            if task_tags:
                display_text += f"  [{', '.join(task_tags[:3])}]"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, task_id)
            item.setData(Qt.UserRole + 1, task_tags)
            item.setData(Qt.UserRole + 2, task_name)
            if task_id in selected_ids:
                item.setSelected(True)
            self.prereq_list.addItem(item)
            self._prereq_task_items.append(item)

    def _filter_prerequisite_tasks(self):
        search_text = self.prereq_search_input.text().strip().lower()
        selected_tag = self.prereq_tag_filter.currentData()

        for item in self._prereq_task_items:
            task_name = item.data(Qt.UserRole + 2).lower()
            task_tags = item.data(Qt.UserRole + 1)

            visible = True
            if search_text and search_text not in task_name:
                visible = False
            if selected_tag and selected_tag not in task_tags:
                visible = False

            item.setHidden(not visible)

    def get_tags(self) -> list:
        tags_text = self.tags_input.text().strip()
        if not tags_text:
            return []
        return [tag.strip() for tag in tags_text.split(",") if tag.strip()]

    def get_prerequisite_ids(self) -> list:
        selected_ids = []
        for item in self.prereq_list.selectedItems():
            task_id = item.data(Qt.UserRole)
            selected_ids.append(task_id)
        return selected_ids

    def get_task(self) -> Task:
        task = Task(
            name=self.name_input.text(),
            category=self.task_type_combo.currentData(),
            description=self.desc_input.toPlainText(),
            estimated_time=self.time_input.value(),
            deadline=self.deadline_input.text() or None,
            resistance=self.resistance_combo.currentData(),
            energy_required=self.energy_combo.currentData(),
            priority=self.priority_spin.value(),
            is_daily=self.is_daily_check.isChecked(),
            tags=self.get_tags(),
            prerequisite_ids=self.get_prerequisite_ids()
        )
        if self.task:
            task.id = self.task.id
        return task


class DiscardPileDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()
        self._load_tasks()

    def _init_ui(self):
        self.setWindowTitle("🗑️ 弃牌堆")
        self.resize(650, 550)
        self.setStyleSheet(MODERN_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        title_layout = QHBoxLayout()
        title_icon = QLabel("🗑️")
        title_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(title_icon)

        title = QLabel("弃牌堆")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2C3E50;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.count_label = QLabel("0 张卡")
        self.count_label.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        title_layout.addWidget(self.count_label)

        main_layout.addLayout(title_layout)

        info = QLabel("💡 每日任务明天会自动回到抽牌堆 · 每周任务下周会自动回到抽牌堆")
        info.setStyleSheet("color: #7F8C8D; font-size: 12px;")
        main_layout.addWidget(info)

        self.card_container = QScrollArea()
        self.card_container.setWidgetResizable(True)
        self.card_container.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.card_widget = QWidget()
        self.card_layout = QVBoxLayout(self.card_widget)
        self.card_layout.setSpacing(-40)
        self.card_layout.setContentsMargins(10, 10, 10, 60)

        self.card_container.setWidget(self.card_widget)
        main_layout.addWidget(self.card_container)

        btn_layout = QHBoxLayout()

        self.pick_btn = QPushButton("🎴 抓回抽牌堆")
        self.pick_btn.clicked.connect(self._pick_selected)
        self.pick_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_layout.addWidget(self.pick_btn)

        reset_all_btn = QPushButton("🔄 重置全部")
        reset_all_btn.clicked.connect(self._reset_all)
        reset_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        btn_layout.addWidget(reset_all_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

    def _load_tasks(self):
        for i in reversed(range(self.card_layout.count())):
            item = self.card_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()

        tasks = self.db.get_discard_pile_tasks()

        if not tasks:
            empty_label = QLabel("（暂无弃牌堆任务）")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("font-size: 16px; color: #bdc3c7; padding: 40px;")
            self.card_layout.addWidget(empty_label)
            self.pick_btn.setEnabled(False)
            self.count_label.setText("0 张卡")
            return

        self.pick_btn.setEnabled(True)
        self.count_label.setText(f"{len(tasks)} 张卡")

        from ..models.task import TaskProfile

        for idx, task in enumerate(tasks):
            card_frame = QFrame()
            task_profile = task.get('task_profile', 'deadline_flexible')
            profile_colors = {
                'daily_habit': '#7F8C8D',
                'weekly_routine': '#27AE60',
                'deadline_flexible': '#2980B9',
                'deadline_progressive': '#E74C3C',
            }
            border_color = profile_colors.get(task_profile, '#4A90E2')

            margin_top = 80 if idx > 0 else 0
            card_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 2px solid {border_color};
                    border-radius: 12px;
                    padding: 15px;
                    margin-top: {margin_top}px;
                }}
                QFrame:hover {{
                    border-width: 3px;
                }}
            """)

            card_layout = QHBoxLayout(card_frame)

            info_layout = QVBoxLayout()

            name_label = QLabel(task['name'])
            name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
            info_layout.addWidget(name_label)

            details = []
            estimated_time = task.get('estimated_time', 0)
            details.append(f"⏱️ {estimated_time}分钟")
            repeat_type = task.get('repeat_type', 'none')
            repeat_display = {
                'daily': '🔄 每日',
                'weekly': '📅 每周',
                'accumulation': '📚 复习'
            }.get(repeat_type, '')
            if repeat_display:
                details.append(repeat_display)

            tags = task.get('tags', [])
            if tags:
                details.append(f"🏷️ {', '.join(tags[:2])}")

            detail_label = QLabel(" | ".join(details))
            detail_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
            info_layout.addWidget(detail_label)

            card_layout.addLayout(info_layout)
            card_layout.addStretch()

            check_btn = QPushButton("选择")
            check_btn.setFixedSize(80, 30)
            check_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2980B9;
                }
            """)
            check_btn.clicked.connect(lambda checked, tid=task['id']: self._pick_task(tid))
            card_layout.addWidget(check_btn)

            self.card_layout.addWidget(card_frame)

        self.card_layout.addStretch()

    def _pick_task(self, task_id: int):
        self.db.move_task_to_gacha_pile(task_id)
        QMessageBox.information(self, "成功", "✅ 任务已抓回抽牌堆！")
        self._load_tasks()

    def _pick_selected(self):
        if self.card_layout.count() > 0:
            first_item = self.card_layout.itemAt(0)
            if first_item and first_item.widget():
                pass
        self._load_tasks()

    def _reset_all(self):
        reply = QMessageBox.question(
            self,
            "确认重置",
            "确定要将所有任务从弃牌堆抓回吗？"
        )
        if reply == QMessageBox.Yes:
            cursor = self.db.conn.cursor()
            cursor.execute("UPDATE tasks SET in_discard_pile = 0 WHERE in_discard_pile = 1")
            self.db.conn.commit()
            QMessageBox.information(self, "成功", "✅ 弃牌堆已全部重置！")
            self._load_tasks()


class DailyToneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_tone = DailyTone.NORMAL
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("早上好")
        self.setFixedSize(500, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                background-color: white;
                color: #2c3e50;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                padding: 15px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #4A90E2;
                background-color: #EBF5FB;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("☀️ 早上好，今天感觉怎么样？")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("选择今天的节奏，我会根据你的状态调整推荐")
        subtitle.setStyleSheet("font-size: 13px; color: #7f8c8d;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        tones = [
            (DailyTone.HIGH, "⚡ 高效日", "适合挑战难题"),
            (DailyTone.NORMAL, "☀️ 普通日", "常规节奏"),
            (DailyTone.LOW, "🌙 低负荷", "只做轻松的事"),
            (DailyTone.REST, "🏖️ 休息日", "今天不做事"),
        ]

        for value, name, desc in tones:
            btn = QPushButton(f"<b>{name}</b><br><small>{desc}</small>")
            btn.clicked.connect(lambda checked, v=value: self._select(v))
            layout.addWidget(btn)

        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(lambda: self._select(DailyTone.NORMAL))
        self.auto_close_timer.start(10000)

        note = QLabel("⏳ 10秒内不选择将自动设为普通日")
        note.setStyleSheet("font-size: 11px; color: #bdc3c7;")
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

    def _select(self, tone: str):
        self.selected_tone = tone
        self.accept()


class CompletionFeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.energy_value = 7
        self.mood_value = 0
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("完成反馈")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                border: 2px solid #e0e0e0;
                border-radius: 20px;
                padding: 10px;
                font-size: 18px;
                min-width: 50px;
            }
            QPushButton:hover {
                border-color: #4A90E2;
                background-color: #EBF5FB;
            }
            QPushButton:checked {
                border-color: #4A90E2;
                background-color: #D6EAF8;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4A90E2;
                width: 20px;
                height: 20px;
                margin: -7px 0;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        title = QLabel("干得不错！刚才状态怎么样？")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        from PySide6.QtWidgets import QSlider
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(1, 10)
        self.energy_slider.setValue(7)
        self.energy_slider.setTickPosition(QSlider.TicksBelow)
        self.energy_slider.setTickInterval(1)
        layout.addWidget(self.energy_slider)

        slider_label = QLabel("精力状态（1-10）")
        slider_label.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        slider_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(slider_label)

        mood_layout = QHBoxLayout()
        mood_layout.setSpacing(15)
        mood_layout.addStretch()

        moods = [
            ("😞", -1),
            ("😐", 0),
            ("😊", 1),
        ]
        self.mood_btns = []
        for emoji, val in moods:
            btn = QPushButton(emoji)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=val: self._select_mood(v, moods))
            self.mood_btns.append(btn)
            mood_layout.addWidget(btn)

        mood_layout.addStretch()
        layout.addLayout(mood_layout)

        mood_label = QLabel("心情（可选）")
        mood_label.setStyleSheet("font-size: 11px; color: #bdc3c7;")
        mood_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(mood_label)

        btn_layout = QHBoxLayout()

        skip_btn = QPushButton("跳过")
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
                border: none;
                font-size: 14px;
                padding: 8px 20px;
            }
        """)
        skip_btn.clicked.connect(self.reject)

        submit_btn = QPushButton("提交")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                font-size: 14px;
                padding: 8px 20px;
            }
        """)
        submit_btn.clicked.connect(self.accept)

        btn_layout.addWidget(skip_btn)
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)

        self.auto_timer = QTimer()
        self.auto_timer.setSingleShot(True)
        self.auto_timer.timeout.connect(self.accept)
        self.auto_timer.start(3000)

    def _select_mood(self, val, moods):
        self.mood_value = val

    def get_feedback(self):
        return {
            "energy": self.energy_slider.value(),
            "mood": self.mood_value
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.task_service = TaskService(self.db)
        self.state_service = StateService(self.db)
        self.ai_import_processor = AIImportProcessor(self.db)
        self.current_task = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timer)
        self.remaining_seconds = 0

        self._init_ui()
        self._check_and_process_ai_imports()
        self._check_periodic_tasks()
        self._check_daily_tone()
        QTimer.singleShot(500, self._check_sleep_confirm)

    def _check_and_process_ai_imports(self):
        results, processed_files = self.ai_import_processor.process_all_imports()
        if results:
            summary_text = ""
            for result in results:
                summary_text += f"• {result['explanation']}\n"
            self._show_ai_summary(summary_text)
            self.ai_import_processor.delete_processed_files(processed_files)

    def _show_ai_summary(self, summary_text):
        from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
        summary_text = summary_text.strip()
        if summary_text:
            self.ai_summary_label.setText(summary_text)
            self.ai_summary_frame.setVisible(True)
        else:
            self.ai_summary_frame.setVisible(False)

    def _export_system_config(self):
        config = self.ai_import_processor.export_system_config()
        import json
        from datetime import datetime
        from pathlib import Path
        
        ai_exports_dir = Path(__file__).parent.parent.parent / "ai_exports"
        ai_exports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = ai_exports_dir / f"system_config_{timestamp}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        QMessageBox.information(self, "导出成功", f"系统配置已导出到:\n{filepath}")

    def _check_daily_tone(self):
        from datetime import date
        today = date.today()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT daily_tone FROM daily_user_state WHERE date = ?", (today.isoformat(),))
        row = cursor.fetchone()
        if not row:
            self.state_service.set_daily_tone(DailyTone.NORMAL, today)
        self._update_status_bar()
        if self.state_service.is_rest_day(today):
            self._reset_task_display("🏖️ 今日休息 - 系统已暂停任务推送")
            self.start_btn.setEnabled(False)
            self.complete_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)

    def _update_status_bar(self):
        from datetime import date
        today = date.today()
        tone = self.state_service.get_daily_tone(today)
        tone_icons = {
            DailyTone.HIGH: "⚡",
            DailyTone.NORMAL: "☀️",
            DailyTone.LOW: "🌙",
            DailyTone.REST: "🏖️",
        }
        tone_icon = tone_icons.get(tone, "☀️")
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE completed = 1 AND date(updated_at) = date('now')")
        done_count = cursor.fetchone()['cnt']
        
        sleep_streak = self.state_service.get_sleep_early_streak()
        sleep_text = f" 🌙 {sleep_streak}天" if sleep_streak > 0 else ""
        
        stars = " ⭐" * min(sleep_streak // 3, 3) if sleep_streak >= 3 else ""
        
        self.status_bar_label.setText(
            f"{tone_icon} {tone}  |  ✅ 今日完成 {done_count} 个任务{sleep_text}{stars}"
        )

    def _check_sleep_confirm(self):
        from datetime import date, datetime, timedelta
        today = date.today()
        yesterday = (today - timedelta(days=1)).isoformat()
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT bed_time, sleep_early_streak FROM daily_user_state WHERE date = ?", (yesterday,))
        recorded = cursor.fetchone()
        
        cursor.execute("SELECT bed_time FROM daily_user_state WHERE date = ?", (today.isoformat(),))
        today_recorded = cursor.fetchone()
        
        if today_recorded and today_recorded['bed_time']:
            return
        
        if recorded and recorded['bed_time']:
            reply = QMessageBox.question(
                self,
                "早睡确认",
                "昨晚大约几点睡的？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                dialog = QDialog(self)
                dialog.setWindowTitle("昨晚几点睡的？")
                dialog.setFixedSize(350, 200)
                layout = QVBoxLayout(dialog)
                layout.setSpacing(15)
                
                title = QLabel("昨晚大约几点睡的？")
                title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
                title.setAlignment(Qt.AlignCenter)
                layout.addWidget(title)
                
                btn_layout = QHBoxLayout()
                
                def set_time(q, label):
                    self.state_service.record_sleep_time(q, label, yesterday)
                    dialog.accept()
                
                options = [
                    ("on_time", "⏰ 按时"),
                    ("late", "🌙 稍晚"),
                    ("very_late", "🌚 很晚"),
                ]
                for value, display in options:
                    btn = QPushButton(display)
                    btn.clicked.connect(lambda checked, v=value, d=display: set_time(v, d))
                    btn_layout.addWidget(btn)
                
                layout.addLayout(btn_layout)
                dialog.exec()
                self._update_status_bar()

    def _init_ui(self):
        self.setWindowTitle("🎯 任务随机发布器")
        self.resize(900, 750)
        self.setStyleSheet(MODERN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🎯 任务随机发布器")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 状态栏
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #EBF5FB;
                border: 1px solid #AED6F1;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 5, 15, 5)

        self.status_bar_label = QLabel("☀️ 普通日  |  ✅ 今日完成 0 个任务")
        self.status_bar_label.setStyleSheet("font-size: 13px; color: #2c3e50;")
        status_layout.addWidget(self.status_bar_label)

        status_layout.addStretch()

        self.replace_indicator = QLabel("今日换牌机会：1次")
        self.replace_indicator.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        status_layout.addWidget(self.replace_indicator)

        main_layout.addWidget(status_frame)

        # AI 处理总结区域
        self.ai_summary_frame = QFrame()
        self.ai_summary_frame.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border: 2px solid #81C784;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        ai_summary_layout = QVBoxLayout(self.ai_summary_frame)
        
        ai_title = QLabel("🤖 AI 处理结果")
        ai_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2E7D32;")
        ai_summary_layout.addWidget(ai_title)
        
        self.ai_summary_label = QLabel("")
        self.ai_summary_label.setStyleSheet("font-size: 13px; color: #2E7D32;")
        self.ai_summary_label.setWordWrap(True)
        ai_summary_layout.addWidget(self.ai_summary_label)
        
        main_layout.addWidget(self.ai_summary_frame)
        self.ai_summary_frame.setVisible(False)

        # 主抽卡按钮 - 玻璃拟态风格
        from PySide6.QtGui import QPainter, QColor, QLinearGradient, QFont, QBrush, QPen, QRadialGradient, QPainterPath
        from PySide6.QtCore import QRectF, QPropertyAnimation, QEasingCurve, Signal, Property, QPoint
        
        class GlassGachaButton(QWidget):
            def __init__(self, text, parent=None):
                super().__init__(parent)
                self.text = text
                self.is_hovered = False
                self.is_pressed = False
                self._glow_intensity = 0.4
                self._particles = []
                self.setFixedSize(200, 200)
                
                self._setup_animations()
                self._init_particles()
            
            def _setup_animations(self):
                self.glow_animation = QPropertyAnimation(self, b"glow_intensity")
                self.glow_animation.setDuration(2500)
                self.glow_animation.setStartValue(0.3)
                self.glow_animation.setEndValue(0.6)
                self.glow_animation.setLoopCount(-1)
                self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)
                self.glow_animation.start()
            
            def _init_particles(self):
                import random
                for _ in range(12):
                    self._particles.append({
                        'x': random.uniform(10, 190),
                        'y': random.uniform(10, 190),
                        'vx': (random.random() - 0.5) * 0.3,
                        'vy': (random.random() - 0.5) * 0.3,
                        'size': random.uniform(1, 2),
                        'alpha': random.uniform(0.3, 0.7),
                        'pulse': random.uniform(0, 360)
                    })
            
            def get_glow_intensity(self):
                return self._glow_intensity
            
            def set_glow_intensity(self, value):
                self._glow_intensity = value
                self.update()
            
            glow_intensity = Property(float, get_glow_intensity, set_glow_intensity)
            
            def _fill_rounded_rect(self, painter, rect, radius, brush):
                path = QPainterPath()
                path.addRoundedRect(rect, radius, radius)
                painter.fillPath(path, brush)
            
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)
                
                rect = self.rect()
                shadow_offset = 8 if not self.is_pressed else 4
                button_offset = 4 if self.is_pressed else 0
                scale_factor = 1.02 if self.is_hovered and not self.is_pressed else 1.0
                
                painter.save()
                painter.translate(0, shadow_offset)
                shadow_rect = rect.adjusted(8, 8, -8, -8)
                shadow_grad = QRadialGradient(shadow_rect.center(), shadow_rect.width()/2)
                shadow_grad.setColorAt(0, QColor(0, 0, 0, 80))
                shadow_grad.setColorAt(0.5, QColor(0, 0, 0, 40))
                shadow_grad.setColorAt(1, QColor(0, 0, 0, 0))
                self._fill_rounded_rect(painter, shadow_rect, 8, shadow_grad)
                painter.restore()
                
                painter.save()
                painter.translate(rect.center().x(), rect.center().y())
                painter.scale(scale_factor, scale_factor)
                painter.translate(-rect.center().x(), -rect.center().y())
                painter.translate(0, button_offset)
                
                center_x = rect.center().x()
                center_y = rect.center().y()
                
                diamond_size = 120
                diamond_half_size = diamond_size / 2
                
                painter.save()
                painter.translate(center_x, center_y)
                painter.rotate(45)
                
                diamond_rect = QRectF(-diamond_half_size, -diamond_half_size, diamond_size, diamond_size)
                
                glass_bg = QLinearGradient(diamond_rect.topLeft(), diamond_rect.bottomRight())
                glass_bg.setColorAt(0, QColor(40, 45, 55, 180))
                glass_bg.setColorAt(0.5, QColor(30, 35, 45, 160))
                glass_bg.setColorAt(1, QColor(25, 30, 40, 180))
                
                painter.fillRect(diamond_rect, glass_bg)
                
                for i in range(30):
                    for j in range(30):
                        noise_val = (i * 13 + j * 17) % 256
                        if noise_val > 245:
                            x = diamond_rect.left() + (i / 30) * diamond_rect.width()
                            y = diamond_rect.top() + (j / 30) * diamond_rect.height()
                            painter.setPen(QPen(QColor(80, 90, 110, 40), 1))
                            painter.drawPoint(x, y)
                
                gold_border_grad = QLinearGradient(diamond_rect.topLeft(), diamond_rect.bottomRight())
                gold_border_grad.setColorAt(0, QColor("#d4af37"))
                gold_border_grad.setColorAt(0.3, QColor("#f4d03f"))
                gold_border_grad.setColorAt(0.5, QColor("#d4af37"))
                gold_border_grad.setColorAt(0.7, QColor("#c9a227"))
                gold_border_grad.setColorAt(1, QColor("#b8941f"))
                
                painter.setPen(QPen(QBrush(gold_border_grad), 3))
                painter.drawRect(diamond_rect)
                
                inner_diamond = diamond_rect.adjusted(12, 12, -12, -12)
                
                inner_grad = QLinearGradient(inner_diamond.topLeft(), inner_diamond.bottomRight())
                inner_grad.setColorAt(0, QColor(60, 70, 90, 80))
                inner_grad.setColorAt(0.5, QColor(40, 50, 70, 60))
                inner_grad.setColorAt(1, QColor(30, 40, 60, 80))
                
                painter.setOpacity(0.6)
                painter.fillRect(inner_diamond, inner_grad)
                painter.setOpacity(1.0)
                
                text_glow_radius = inner_diamond.width() * 0.5
                text_glow_grad = QRadialGradient(0, 0, text_glow_radius)
                glow_intensity = self._glow_intensity * (1.3 if self.is_hovered else 1.0)
                text_glow_grad.setColorAt(0, QColor(255, 215, 100, int(80 * glow_intensity)))
                text_glow_grad.setColorAt(0.4, QColor(255, 180, 50, int(40 * glow_intensity)))
                text_glow_grad.setColorAt(0.7, QColor(255, 150, 30, int(20 * glow_intensity)))
                text_glow_grad.setColorAt(1, QColor(255, 120, 20, 0))
                
                painter.fillRect(inner_diamond, text_glow_grad)
                
                painter.restore()
                
                for particle in self._particles:
                    particle_x = particle['x']
                    particle_y = particle['y']
                    distance = ((particle_x - rect.center().x())**2 + (particle_y - rect.center().y())**2)**0.5
                    max_distance = diamond_size * 0.7
                    
                    if distance < max_distance:
                        particle_alpha = particle['alpha'] * (1 - distance / max_distance) * glow_intensity
                        if self.is_hovered:
                            particle_alpha *= 1.5
                        
                        painter.setPen(QPen(QColor(200, 210, 230, int(150 * particle_alpha)), particle['size']))
                        painter.drawPoint(particle_x, particle_y)
                
                painter.restore()
                
                text_font = QFont("Segoe UI", 28, QFont.Medium)
                text_font.setLetterSpacing(QFont.AbsoluteSpacing, 10)
                text_font.setStyleStrategy(QFont.PreferAntialias)
                painter.setFont(text_font)
                
                gold_text_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
                gold_text_grad.setColorAt(0, QColor("#e8d5a3"))
                gold_text_grad.setColorAt(0.3, QColor("#f5e6b8"))
                gold_text_grad.setColorAt(0.5, QColor("#d4c494"))
                gold_text_grad.setColorAt(0.7, QColor("#e8d5a3"))
                gold_text_grad.setColorAt(1, QColor("#c9b58a"))
                
                painter.setPen(QPen(QBrush(gold_text_grad), 2))
                painter.drawText(self.rect(), Qt.AlignCenter, self.text)
                
                inner_glow_intensity = glow_intensity * 0.5
                inner_pen = QPen(QColor(255, 230, 180, int(100 * inner_glow_intensity)))
                inner_pen.setWidth(1)
                painter.setPen(inner_pen)
                painter.drawText(self.rect(), Qt.AlignCenter, self.text)
            
            def enterEvent(self, event):
                self.is_hovered = True
                self.update()
            
            def leaveEvent(self, event):
                self.is_hovered = False
                self.update()
            
            def mousePressEvent(self, event):
                self.is_pressed = True
                self.update()
            
            def mouseReleaseEvent(self, event):
                self.is_pressed = False
                self.update()
                self.clicked.emit()
            
            def update_particles(self):
                center_x = self.width() / 2
                center_y = self.height() / 2
                max_distance = self.width() * 0.45
                
                for particle in self._particles:
                    particle['x'] += particle['vx']
                    particle['y'] += particle['vy']
                    particle['pulse'] += 2
                    
                    distance = ((particle['x'] - center_x)**2 + (particle['y'] - center_y)**2)**0.5
                    if distance > max_distance:
                        import random
                        particle['x'] = center_x + (random.random() - 0.5) * max_distance * 0.5
                        particle['y'] = center_y + (random.random() - 0.5) * max_distance * 0.5
                
                self.update()
                
                from PySide6.QtCore import QTimer
                QTimer.singleShot(50, self.update_particles)
        
        GlassGachaButton.clicked = Signal()
        
        gacha_main_layout = QVBoxLayout()
        gacha_main_layout.setContentsMargins(50, 50, 50, 50)
        
        self.gacha_btn = GlassGachaButton("抽卡")
        self.gacha_btn.clicked.connect(self._open_gacha)
        self.gacha_btn.update_particles()
        gacha_main_layout.addWidget(self.gacha_btn, alignment=Qt.AlignCenter)
        
        main_layout.addLayout(gacha_main_layout)

        # 辅助功能按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        btn_layout.setAlignment(Qt.AlignCenter)

        self.schedule_btn = QPushButton("📅 日程安排")
        self.schedule_btn.clicked.connect(self._open_schedule)
        self.schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        btn_layout.addWidget(self.schedule_btn)

        self.export_btn = QPushButton("📤 导出数据")
        self.export_btn.clicked.connect(self._export_data)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        btn_layout.addWidget(self.export_btn)

        self.config_btn = QPushButton("🔧 导出配置")
        self.config_btn.clicked.connect(self._export_system_config)
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #795548;
            }
            QPushButton:hover {
                background-color: #5D4037;
            }
        """)
        btn_layout.addWidget(self.config_btn)

        self.dep_graph_btn = QPushButton("🔗 依赖图")
        self.dep_graph_btn.clicked.connect(self._open_dependency_graph)
        self.dep_graph_btn.setStyleSheet("""
            QPushButton {
                background-color: #1ABC9C;
            }
            QPushButton:hover {
                background-color: #16A085;
            }
        """)
        btn_layout.addWidget(self.dep_graph_btn)

        main_layout.addLayout(btn_layout)

        task_frame = QFrame()
        task_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #E0E0E0;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        task_layout = QVBoxLayout(task_frame)
        task_layout.setSpacing(15)

        self.task_card_container = QHBoxLayout()
        self.task_card_container.setAlignment(Qt.AlignCenter)
        self.task_card_container.setSpacing(20)

        self.placeholder_label = QLabel("等待抽取...")
        self.placeholder_label.setFont(QFont("Microsoft YaHei", 14))
        self.placeholder_label.setStyleSheet("color: #95a5a6; background: transparent;")
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.task_card_container.addWidget(self.placeholder_label)

        self.task_cards = []
        task_layout.addLayout(self.task_card_container)

        self.sleep_warning_label = QLabel("")
        self.sleep_warning_label.setStyleSheet("font-size: 12px; color: #E74C3C; background: transparent;")
        self.sleep_warning_label.setAlignment(Qt.AlignCenter)
        self.sleep_warning_label.setWordWrap(True)
        self.sleep_warning_label.hide()
        task_layout.addWidget(self.sleep_warning_label)

        self.task_info_label = QLabel("")
        self.task_info_label.setStyleSheet("font-size: 12px; color: #7f8c8d; background: transparent;")
        self.task_info_label.setAlignment(Qt.AlignCenter)
        self.task_info_label.setWordWrap(True)
        task_layout.addWidget(self.task_info_label)

        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("TimerLabel")
        self.timer_label.setAlignment(Qt.AlignCenter)
        task_layout.addWidget(self.timer_label)

        timer_btn_layout = QHBoxLayout()
        timer_btn_layout.setSpacing(15)

        self.start_btn = QPushButton("▶️ 开始番茄钟")
        self.start_btn.clicked.connect(self._start_timer)
        self.start_btn.setEnabled(False)
        timer_btn_layout.addWidget(self.start_btn)

        self.complete_btn = QPushButton("✅ 完成任务")
        self.complete_btn.clicked.connect(self._complete_task)
        self.complete_btn.setEnabled(False)
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        timer_btn_layout.addWidget(self.complete_btn)

        self.skip_btn = QPushButton("🔄 跳过")
        self.skip_btn.clicked.connect(self._skip_task)
        self.skip_btn.setEnabled(False)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        timer_btn_layout.addWidget(self.skip_btn)

        task_layout.addLayout(timer_btn_layout)
        main_layout.addWidget(task_frame)

    def _add_task(self):
        dialog = TaskEditDialog(self, db=self.db)
        if dialog.exec():
            task = dialog.get_task()
            prerequisite_ids = task.prerequisite_ids

            if prerequisite_ids:
                temp_id = -1
                if self.task_service.detect_cycle(temp_id, prerequisite_ids):
                    QMessageBox.warning(self, "循环依赖", "❌ 检测到循环依赖！请重新选择前置任务。")
                    return

            task_id = self.task_service.add_task(task)
            if task.tags:
                self.db.set_task_tags(task_id, task.tags)
            QMessageBox.information(self, "成功", "✅ 任务添加成功！")

    def _edit_task(self, item):
        task_id = item.data(Qt.UserRole)
        task_dict = self.db.get_task(task_id)
        if task_dict:
            task_dict['tags'] = task_dict.get('tags', [])
            task = Task.from_dict(task_dict)
            dialog = TaskEditDialog(self, task=task, db=self.db)
            if dialog.exec():
                updated_task = dialog.get_task()

                prerequisite_ids = updated_task.prerequisite_ids or []
                if prerequisite_ids:
                    if self.task_service.detect_cycle(task_id, prerequisite_ids):
                        QMessageBox.warning(self, "循环依赖", "❌ 检测到循环依赖！请重新选择前置任务。")
                        return

                update_kwargs = {
                    'name': updated_task.name,
                    'category': updated_task.category,
                    'task_type': updated_task.task_type,
                    'description': updated_task.description,
                    'estimated_time': updated_task.estimated_time,
                    'deadline': updated_task.deadline,
                    'resistance': updated_task.resistance,
                    'energy_required': updated_task.energy_required,
                    'priority': updated_task.priority,
                    'is_daily': updated_task.is_daily,
                    'tags': updated_task.tags,
                    'prerequisite_ids': prerequisite_ids
                }

                if prerequisite_ids:
                    is_unlocked = all(
                        (self.db.get_task(pid) or {}).get('completed', False)
                        for pid in prerequisite_ids
                    )
                    update_kwargs['is_unlocked'] = is_unlocked
                else:
                    update_kwargs['is_unlocked'] = True

                self.db.update_task(task_id, **update_kwargs)

    def _open_gacha(self):
        self.gacha_window = GachaWindow(self.db, self)
        self.gacha_window.task_selected.connect(self._on_task_selected)
        self.gacha_window.show()

    def _reset_task_display(self, placeholder_text=None):
        for card in self.task_cards:
            self.task_card_container.removeWidget(card)
            card.deleteLater()
        self.task_cards.clear()
        if placeholder_text:
            self.placeholder_label.setText(placeholder_text)
        self.placeholder_label.show()
        self.sleep_warning_label.hide()
        self.task_info_label.show()
        self.timer_label.show()

    def _on_task_selected(self, task):
        self.current_task = task
        tags = task.tags if hasattr(task, 'tags') and task.tags else []
        tags_str = ""
        if tags:
            tags_str = f"🏷️ {', '.join(tags)}"

        sleep_warning = ""
        if task.estimated_time:
            from datetime import datetime, date
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT bed_time FROM daily_user_state WHERE date = ?", (date.today().isoformat(),))
            row = cursor.fetchone()
            if row and row['bed_time']:
                try:
                    now = datetime.now()
                    bed_hour = int(row['bed_time'].split(':')[0])
                    bed_min = int(row['bed_time'].split(':')[1])
                    bed_dt = now.replace(hour=bed_hour, minute=bed_min, second=0)
                    time_to_bed = (bed_dt - now).total_seconds() / 60
                    if time_to_bed > 0 and task.estimated_time > time_to_bed:
                        sleep_warning = '⚠️ 预计完成时间将超过你的睡觉时间'
                except:
                    pass

        self.placeholder_label.hide()
        self.task_info_label.hide()
        self.timer_label.hide()

        new_card = StyleIsolationWidget()
        card = CardWidget(task)
        new_card.layout().addWidget(card)
        
        self.task_cards.append(new_card)
        self.task_card_container.addWidget(new_card)
        
        self.current_task = task

        if sleep_warning:
            self.sleep_warning_label.setText(sleep_warning)
            self.sleep_warning_label.show()
        else:
            self.sleep_warning_label.hide()

        self.start_btn.setEnabled(True)
        self.complete_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.remaining_seconds = task.estimated_time * 60
        self._update_timer_display()
        self.replace_indicator.setText("今日换牌机会：已使用")
        QTimer.singleShot(3000, lambda: self.replace_indicator.setText("今日换牌机会：1次"))

    def _pick_random_task(self):
        task = self.task_service.get_random_task()
        if task:
            self._on_task_selected(task)
        else:
            QMessageBox.information(self, "提示", "暂无可用任务，请先添加任务！")

    def _open_schedule(self):
        self.schedule_window = ScheduleWindow(self.db, self)
        self.schedule_window.show()

    def _open_dependency_graph(self):
        dialog = DependencyGraphDialog(self.db, self)
        dialog.exec()

    def _open_discard_pile(self):
        dialog = DiscardPileDialog(self.db, self)
        dialog.exec()

    def _start_timer(self):
        if self.timer.isActive():
            self.timer.stop()
            self.start_btn.setText("▶️ 继续")
        else:
            if self.remaining_seconds == 0:
                self.remaining_seconds = (self.current_task.estimated_time or 25) * 60
            self.timer.start(1000)
            self.start_btn.setText("⏸️ 暂停")

    def _update_timer(self):
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.start_btn.setText("▶️ 开始番茄钟")
            QMessageBox.information(self, "完成！", "⏰ 时间到！任务完成了吗？")
        self._update_timer_display()

    def _update_timer_display(self):
        minutes = self.remaining_seconds // 60
        seconds = self.remaining_seconds % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _complete_task(self):
        if self.current_task:
            unlocked_names = self.task_service.mark_completed(self.current_task.id)

            feedback = CompletionFeedbackDialog(self)
            if feedback.exec():
                fb = feedback.get_feedback()
                cursor = self.db.conn.cursor()
                cursor.execute('''
                    INSERT INTO task_completion_feedback (task_id, energy_after, mood_after, timestamp)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (self.current_task.id, fb['energy'], fb['mood']))
                self.db.conn.commit()

            self.current_task = None
            self._reset_task_display("当前任务: 等待抽取...")
            self.timer_label.setText("00:00")
            self.timer.stop()
            self.start_btn.setText("▶️ 开始番茄钟")
            self.start_btn.setEnabled(False)
            self.complete_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)
            self._update_status_bar()

            if unlocked_names:
                names_str = "、".join(unlocked_names)
                QMessageBox.information(self, "新任务已解锁", f"🔓 新任务已解锁：{names_str}")

    def _skip_task(self):
        reply = QMessageBox.question(
            self, "跳过任务",
            "确定要跳过这个任务吗？\n\n"
            "跳过效果等同于完成——会触发后续任务的解锁。\n"
            "任务将在依赖图中显示为「已跳过」。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            unlocked_names = self.task_service.skip_task(self.current_task.id)
            self.current_task = None
            self._reset_task_display("当前任务: 等待抽取...")
            self.timer_label.setText("00:00")
            self.timer.stop()
            self.start_btn.setText("▶️ 开始番茄钟")
            self.start_btn.setEnabled(False)
            self.complete_btn.setEnabled(False)
            self.skip_btn.setEnabled(False)

            if unlocked_names:
                names_str = "、".join(unlocked_names)
                QMessageBox.information(self, "新任务已解锁", f"🔓 新任务已解锁：{names_str}")

    def _export_data(self):
        export_service = ExportService(self.db)
        filepath = export_service.export_all()
        QMessageBox.information(self, "导出成功", f"数据已导出到:\n{filepath}")

    def _import_ai_analysis(self):
        reply = QMessageBox.question(
            self, "导入确认",
            "请确保 AI 输出的文件已放到 ai_imports/ 文件夹中。\n\n点击「是」开始导入。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            results = self.ai_import_processor.process_all_imports()
            if results:
                summary_text = ""
                for result in results:
                    summary_text += f"• {result['explanation']}\n"
                self._show_ai_summary(summary_text)
                QMessageBox.information(self, "导入成功", "AI 分析已导入并应用！")
            else:
                QMessageBox.information(self, "提示", "没有找到新的导入文件。")

    def _set_rest_day(self):
        reply = QMessageBox.question(
            self, "休息日确认",
            "确定今天要休息吗？\n\n系统将暂停今天的任务推送。",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.task_service.set_rest_day()
            QMessageBox.information(self, "休息日", "😴 好的，今天好好休息！\n明天见！")

    def _check_periodic_tasks(self):
        self.task_service.check_and_reset_periodic_tasks()

    def closeEvent(self, event):
        self.timer.stop()
        self.db.close()
        event.accept()


class StyleIsolationWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)


class CardWidget(QFrame):
    def __init__(self, task):
        super().__init__()
        self.task = task
        self._init_ui()

    def _is_urgent(self) -> bool:
        if hasattr(self.task, 'task_profile') and self.task.task_profile == "deadline_progressive":
            return True
        if hasattr(self.task, 'deadline') and self.task.deadline:
            try:
                from datetime import datetime
                deadline_dt = datetime.fromisoformat(self.task.deadline)
                return (deadline_dt - datetime.now()).days <= 1 or deadline_dt <= datetime.now()
            except:
                pass
        return False

    def _card_color(self) -> tuple:
        if self._is_urgent():
            return (220, 53, 69), (185, 28, 28)
        return (33, 150, 243), (66, 165, 245)

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        self.setGraphicsEffect(shadow)

    def _init_ui(self):
        base_color, border_color = self._card_color()

        self.setFixedSize(200, 280)
        self.setStyleSheet(f"""
            CardWidget {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba({base_color[0]}, {base_color[1]}, {base_color[2]}, 0.85),
                    stop:0.4 rgba({border_color[0]}, {border_color[1]}, {border_color[2]}, 0.7),
                    stop:0.7 rgba(200, 230, 255, 0.6),
                    stop:1 rgba(255, 255, 255, 0.5));
                border: 1.5px solid rgba(255, 255, 255, 0.6);
                border-radius: 14px;
            }}
            CardWidget QLabel {{
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(8)

        name_label = QLabel(self.task.name if hasattr(self.task, 'name') else "未命名任务")
        name_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        name_label.setStyleSheet(f"""
            color: {'#FFFFFF' if self._is_urgent() else '#1E3A5F'};
            background: transparent;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
            border: none;
            padding: 0;
        """)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        tags_text = ""
        if hasattr(self.task, 'tags') and self.task.tags:
            tags_text = ", ".join(self.task.tags[:3])
        if tags_text:
            tags_label = QLabel(f"🏷️ {tags_text}")
            tags_label.setFont(QFont("Microsoft YaHei", 9))
            tags_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.85);
                background: transparent;
                border: none;
                padding: 0;
            """)
            tags_label.setAlignment(Qt.AlignCenter)
            tags_label.setWordWrap(True)
            layout.addWidget(tags_label)

        layout.addStretch(1)

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(4)

        resistance = getattr(self.task, 'resistance', 'medium')
        resistance_label = QLabel(f"⚡ 阻力: {resistance}")
        resistance_label.setFont(QFont("Microsoft YaHei", 10))
        resistance_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
            border: none;
            padding: 0;
        """)
        resistance_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(resistance_label)

        energy = getattr(self.task, 'energy_required', 'medium')
        energy_label = QLabel(f"💪 精力: {energy}")
        energy_label.setFont(QFont("Microsoft YaHei", 10))
        energy_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
            border: none;
            padding: 0;
        """)
        energy_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(energy_label)

        layout.addLayout(stats_layout)

        estimated_time = getattr(self.task, 'estimated_time', 25)
        time_label = QLabel(f"⏱ {estimated_time} 分钟")
        time_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        time_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            background: transparent;
            border: none;
            padding: 0;
        """)
        time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(time_label)
