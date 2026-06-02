from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSpinBox, QFrame, QMessageBox,
    QListWidget, QListWidgetItem, QScrollArea, QWidget,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor

from ..models.database import Database
from ..models.task import Task
from ..services.gacha_service import GachaService, GachaPool, GachaSessionContext, DrawResult, DrawChoiceResult


GACHA_STYLE = """
QDialog {
    background-color: #f8f9fa;
}

QLabel {
    color: #2c3e50;
}

QPushButton {
    background-color: #4A90E2;
    color: white;
    border: 2px solid #3a7bc8;
    border-radius: 10px;
    padding: 15px 25px;
    font-size: 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3a7bc8;
}

QSpinBox {
    background-color: white;
    color: #2c3e50;
    border: 2px solid #d1dce6;
    border-radius: 8px;
    padding: 10px;
    font-size: 18px;
}

QListWidget {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 10px;
}

QListWidgetItem {
    padding: 10px;
    border-bottom: 1px solid #eee;
}
"""


class CardWidget(QFrame):
    def __init__(self, task: Task):
        super().__init__()
        self.task = task
        self._init_ui()
        QTimer.singleShot(50, self.animate_appear)

    def _is_urgent(self) -> bool:
        if self.task.task_profile == "deadline_progressive":
            return True
        if self.task.deadline:
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

    def animate_appear(self):
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(400)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.OutCubic)

        start_geo = self.geometry()
        self.move(self.pos().x(), self.pos().y() + 30)
        self._slide_up = QPropertyAnimation(self, b"pos")
        self._slide_up.setDuration(400)
        self._slide_up.setStartValue(self.pos())
        self._slide_up.setEndValue(start_geo.topLeft())
        self._slide_up.setEasingCurve(QEasingCurve.OutCubic)

        self._fade_in.finished.connect(self._apply_shadow)
        self._fade_in.start()
        self._slide_up.start()

    def _init_ui(self):
        base_color, border_color = self._card_color()

        self.setFixedSize(200, 280)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:1, x2:0, y2:0,
                    stop:0 rgba({base_color[0]}, {base_color[1]}, {base_color[2]}, 0.85),
                    stop:0.4 rgba({border_color[0]}, {border_color[1]}, {border_color[2]}, 0.7),
                    stop:0.7 rgba(200, 230, 255, 0.6),
                    stop:1 rgba(255, 255, 255, 0.5));
                border: 1.5px solid rgba(255, 255, 255, 0.6);
                border-radius: 14px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(8)

        name_label = QLabel(self.task.name)
        name_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        name_label.setStyleSheet(f"""
            color: {'#FFFFFF' if self._is_urgent() else '#1E3A5F'};
            background: transparent;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
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
            tags_label.setStyleSheet("color: rgba(255, 255, 255, 0.85); background: transparent;")
            tags_label.setAlignment(Qt.AlignCenter)
            tags_label.setWordWrap(True)
            layout.addWidget(tags_label)

        layout.addStretch(1)

        stats_layout = QVBoxLayout()
        stats_layout.setSpacing(4)

        resistance_label = QLabel(f"⚡ 阻力: {self.task.resistance}")
        resistance_label.setFont(QFont("Microsoft YaHei", 10))
        resistance_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); background: transparent;")
        resistance_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(resistance_label)

        energy_label = QLabel(f"💪 精力: {self.task.energy_required}")
        energy_label.setFont(QFont("Microsoft YaHei", 10))
        energy_label.setStyleSheet("color: rgba(255, 255, 255, 0.9); background: transparent;")
        energy_label.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(energy_label)

        layout.addLayout(stats_layout)

        time_label = QLabel(f"⏱ {self.task.estimated_time or 25} 分钟")
        time_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        time_label.setStyleSheet("color: rgba(255, 255, 255, 0.95); background: transparent;")
        time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(time_label)


class ChoiceDialog(QDialog):
    def __init__(self, draw_choice: DrawChoiceResult, parent=None):
        super().__init__(parent)
        self.draw_choice = draw_choice
        self.selected_task = None
        self._init_ui()

    def _init_ui(self):
        pool_names = {
            GachaPool.FRAGMENT: "碎片卡池",
            GachaPool.TOMATO: "番茄卡池",
            GachaPool.DEEP: "深度卡池",
        }

        self.setWindowTitle(f"🎴 从 {pool_names.get(self.draw_choice.pool, '')} 中选择")
        self.setMinimumSize(1000, 520)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 25, 30, 25)

        if self.draw_choice.is_urgent:
            urgent_label = QLabel("⏰ 这个任务的DDL马上到了！没有别的选择！")
            urgent_label.setStyleSheet("""
                font-size: 18px; font-weight: bold; color: #E74C3C;
                background-color: #FDEDEC; border-radius: 8px; padding: 12px;
            """)
            urgent_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(urgent_label)

        prompt_label = QLabel("选择你想做的任务：")
        prompt_label.setStyleSheet("font-size: 16px; color: #2c3e50; font-weight: bold;")
        layout.addWidget(prompt_label)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignCenter)

        for task in self.draw_choice.choices:
            card = CardWidget(task)
            select_btn = QPushButton("✅ 选这个")
            select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    border-color: #229954;
                    font-size: 14px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            select_btn.clicked.connect(lambda checked, t=task: self._pick_task(t))
            card.layout().addWidget(select_btn)
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        skip_btn = QPushButton("✖ 都不想要")
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                border-color: #7f8c8d;
                font-size: 14px;
                padding: 10px 25px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        skip_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(skip_btn)
        layout.addLayout(bottom_layout)

    def _pick_task(self, task):
        self.selected_task = task
        self.accept()


class GachaWindow(QDialog):
    task_selected = Signal(Task)

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.gacha_service = GachaService(db)
        self.session_context = GachaSessionContext()
        self.selected_pool = None
        self.drawn_cards = []
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("🎰 抽卡系统")
        self.setMinimumSize(900, 800)
        self.setStyleSheet(GACHA_STYLE)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🎰 任务抽卡系统")
        title.setStyleSheet("font-size: 32px; font-weight: bold; color: #4A90E2;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 功能按钮区域
        func_btn_layout = QHBoxLayout()
        func_btn_layout.setSpacing(15)
        
        self.add_task_btn = QPushButton("➕ 添加任务")
        self.add_task_btn.clicked.connect(self._add_task)
        self.add_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                border-color: #229954;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        func_btn_layout.addWidget(self.add_task_btn)
        
        self.view_pool_btn = QPushButton("📦 查看卡池")
        self.view_pool_btn.clicked.connect(self._view_pool)
        self.view_pool_btn.setStyleSheet("""
            QPushButton {
                background-color: #9B59B6;
                border-color: #8E44AD;
            }
            QPushButton:hover {
                background-color: #8E44AD;
            }
        """)
        func_btn_layout.addWidget(self.view_pool_btn)
        
        self.discard_pile_btn = QPushButton("🗑️ 弃牌堆")
        self.discard_pile_btn.clicked.connect(self._open_discard_pile)
        self.discard_pile_btn.setStyleSheet("""
            QPushButton {
                background-color: #795548;
                border-color: #5D4037;
            }
            QPushButton:hover {
                background-color: #5D4037;
            }
        """)
        func_btn_layout.addWidget(self.discard_pile_btn)
        
        self.random_pick_btn = QPushButton("🎲 随机抽取")
        self.random_pick_btn.clicked.connect(self._random_pick)
        self.random_pick_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                border-color: #D35400;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
        """)
        func_btn_layout.addWidget(self.random_pick_btn)
        
        layout.addLayout(func_btn_layout)

        # 时间输入 + 直接抽卡
        time_frame = QFrame()
        time_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        time_layout = QVBoxLayout(time_frame)
        
        hint_label = QLabel("输入你现在有多少时间，然后直接抽卡：")
        hint_label.setStyleSheet("font-size: 16px; color: #34495e;")
        time_layout.addWidget(hint_label)
        
        time_input_layout = QHBoxLayout()
        time_input_layout.setSpacing(10)
        time_label = QLabel("我有")
        time_label.setStyleSheet("font-size: 20px;")
        time_input_layout.addWidget(time_label)
        
        self.time_input = QSpinBox()
        self.time_input.setRange(1, 480)
        self.time_input.setValue(25)
        self.time_input.setSuffix(" 分钟")
        self.time_input.valueChanged.connect(self._update_pool_hint)
        time_input_layout.addWidget(self.time_input)
        
        min_label = QLabel("可用")
        min_label.setStyleSheet("font-size: 20px;")
        time_input_layout.addWidget(min_label)
        
        self.pool_hint_label = QLabel("→ 番茄卡池")
        self.pool_hint_label.setStyleSheet("font-size: 20px; color: #4A90E2; font-weight: bold;")
        time_input_layout.addWidget(self.pool_hint_label)
        
        # 在时间输入右侧直接放置抽卡按钮
        self.single_btn = QPushButton("🎴 单抽")
        self.single_btn.clicked.connect(self._draw_single)
        self.single_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border-color: #c0392b;
                font-size: 18px;
                padding: 10px 25px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        time_input_layout.addWidget(self.single_btn)
        
        self.multi_btn = QPushButton("🎴🎴🎴 连抽")
        self.multi_btn.clicked.connect(self._draw_multi)
        self.multi_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                border-color: #e67e22;
                font-size: 18px;
                padding: 10px 25px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        time_input_layout.addWidget(self.multi_btn)
        
        time_layout.addLayout(time_input_layout)
        layout.addWidget(time_frame)

        # 结果显示
        self.result_area = QVBoxLayout()
        layout.addLayout(self.result_area)

        self._update_pool_hint()

    def _update_pool_hint(self):
        minutes = self.time_input.value()
        pool = self.gacha_service.get_pool_for_time(minutes)
        if pool:
            pool_names = {
                GachaPool.FRAGMENT: "碎片卡池",
                GachaPool.TOMATO: "番茄卡池",
                GachaPool.DEEP: "深度卡池"
            }
            self.pool_hint_label.setText(f"→ {pool_names[pool]}")
            self.selected_pool = pool
        else:
            self.pool_hint_label.setText("→ 时间不足")
            self.selected_pool = None

    def _draw_single(self):
        if not self.selected_pool:
            QMessageBox.warning(self, "提示", "时间不足，无法抽卡！")
            return

        available_time = self.time_input.value()

        draw_choice = self.gacha_service.draw_single_with_choices(
            self.selected_pool, session_context=self.session_context
        )
        if not draw_choice or not draw_choice.choices:
            QMessageBox.information(self, "提示", "卡池为空！请先添加任务。")
            return

        dialog = ChoiceDialog(draw_choice, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_task:
            selected = dialog.selected_task
            self.gacha_service.record_gacha(self.selected_pool, available_time, selected.id)
            self.session_context.record_draw(selected)
            self._show_single_result(selected)
        else:
            self._show_replace_reason_dialog(draw_choice.choices[0])

    def _show_single_result(self, task):
        self._clear_result_area()

        result_label = QLabel("📋 选中的任务：")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 8px 0;")
        self.result_area.addWidget(result_label)

        card_wrapper = QHBoxLayout()
        card_wrapper.setAlignment(Qt.AlignCenter)

        card = CardWidget(task)
        card_wrapper.addWidget(card)
        self.result_area.addLayout(card_wrapper)

        btn_wrapper = QHBoxLayout()
        btn_wrapper.setAlignment(Qt.AlignCenter)
        btn_wrapper.setSpacing(20)

        confirm_btn = QPushButton("✅ 确认开始")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        confirm_btn.clicked.connect(lambda: self._select_task(task))
        btn_wrapper.addWidget(confirm_btn)

        redraw_btn = QPushButton("🔄 重新抽取")
        redraw_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-size: 14px;
                padding: 8px 20px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        redraw_btn.clicked.connect(self._draw_single)
        btn_wrapper.addWidget(redraw_btn)

        self.result_area.addLayout(btn_wrapper)

    def _draw_multi(self):
        if not self.selected_pool:
            QMessageBox.warning(self, "提示", "时间不足，无法抽卡！")
            return

        available_time = self.time_input.value()
        total_minutes = available_time

        all_results = self.gacha_service.draw_multi_planned(total_minutes)

        if not all_results:
            QMessageBox.information(self, "提示", "卡池为空！请先添加任务。")
            return

        selected_tasks = []
        for draw_result in all_results:
            self.gacha_service.record_gacha(draw_result.pool, total_minutes, draw_result.choices[0].id)
            selected_tasks.append(draw_result.choices[0])

        for task in selected_tasks:
            self.gacha_service._update_draw_count(task.id)

        plans = self.gacha_service.plan_multi_draw(total_minutes)
        plan_summary = " + ".join([
            f"{count}×{GachaPool(p).name if hasattr(GachaPool(p), 'name') else p.value}"
            for p, count in plans
        ])

        info_label = QLabel(f"📋 连抽方案：{plan_summary}")
        info_label.setStyleSheet("""
            font-size: 14px; color: #7f8c8d; padding: 8px;
            background-color: #fef9e7; border: 1px solid #f9e79f;
            border-radius: 6px;
        """)
        self._show_multi_result(selected_tasks, info_label)

        reply = QMessageBox.question(
            self, "连抽完成",
            f"共抽出 {len(selected_tasks)} 个任务！\n是否全部接受并开始第一个？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes and selected_tasks:
            self._select_task(selected_tasks[0])

    def _show_multi_result(self, tasks: list, info_label: QLabel = None):
        for i in reversed(range(self.result_area.count())):
            self.result_area.itemAt(i).widget().deleteLater()

        if info_label:
            wrapper = QFrame()
            wrapper.setStyleSheet("QFrame { background-color: transparent; }")
            w_layout = QVBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.addWidget(info_label)
            self.result_area.addWidget(wrapper)

        result_label = QLabel(f"📊 为你抽出了 {len(tasks)} 个任务：")
        result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 8px 0;")
        self.result_area.addWidget(result_label)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)

        for i, task in enumerate(tasks):
            card = CardWidget(task)

            btn_layout = QHBoxLayout()
            select_btn = QPushButton(f"▶ 开始任务 {i+1}")
            select_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27AE60;
                    border-color: #229954;
                    font-size: 12px;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background-color: #229954;
                }
            """)
            select_btn.clicked.connect(lambda checked, t=task: self._select_task(t))
            btn_layout.addWidget(select_btn)
            card.layout().addLayout(btn_layout)

            cards_layout.addWidget(card)

        wrapper = QFrame()
        wrapper.setStyleSheet("QFrame { background-color: transparent; }")
        w_layout = QVBoxLayout(wrapper)
        w_layout.addLayout(cards_layout)
        self.result_area.addWidget(wrapper)

    def _clear_result_area(self):
        for i in reversed(range(self.result_area.count())):
            item = self.result_area.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _show_replace_reason_dialog(self, task):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("为什么想换？")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        title = QLabel("都不满意？说说原因：")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        reasons = [
            ("low_energy", "🪫 精力不足"),
            ("no_time", "⏰ 时间不够"),
            ("similar_done", "🔄 刚做过类似任务"),
            ("other", "💬 其他"),
        ]
        
        for value, display in reasons:
            btn = QPushButton(display)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    color: #2c3e50;
                    border: 2px solid #bdc3c7;
                    font-size: 14px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #d5dbdb;
                    border-color: #4A90E2;
                }
            """)
            btn.clicked.connect(lambda checked, v=value, d=dialog: self._do_replace_card(task.id, v, d))
            layout.addWidget(btn)
        
        dialog.exec()

    def _do_replace_card(self, task_id: int, reason: str, dialog):
        dialog.accept()
        
        new_result = self.gacha_service.replace_card(
            original_task_id=task_id,
            reason=reason,
            pool=self.selected_pool,
            session_context=self.session_context
        )
        
        if new_result and new_result.task:
            self.gacha_service.record_gacha(self.selected_pool, self.time_input.value(), new_result.task.id)
            self._show_result([new_result])
        else:
            QMessageBox.information(self, "提示", "没有更多可替换的任务。")
    
    def _select_task(self, task):
        self.task_selected.emit(task)
        self.close()

    def _add_task(self):
        from .main_window import TaskEditDialog
        dialog = TaskEditDialog(self, db=self.db)
        if dialog.exec():
            task = dialog.get_task()
            task_id = self.db.add_task(task)
            if task.tags:
                self.db.set_task_tags(task_id, task.tags)
            QMessageBox.information(self, "成功", "✅ 任务添加成功！")

    def _view_pool(self):
        available_tasks = self.db.get_available_tasks_for_gacha()
        self.all_pool_tasks = available_tasks
        
        if not available_tasks:
            QMessageBox.information(self, "卡池", "卡池为空！")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📦 卡池内容")
        dialog.setMinimumSize(700, 550)
        
        layout = QVBoxLayout(dialog)
        
        title_layout = QHBoxLayout()
        title = QLabel(f"卡池中有 {len(available_tasks)} 个任务")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        import_btn = QPushButton("📥 导入JSON")
        import_btn.clicked.connect(lambda: self._import_tasks_json(dialog))
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }
        """)
        title_layout.addWidget(import_btn)
        
        export_btn = QPushButton("📤 导出JSON")
        export_btn.clicked.connect(lambda: self._export_tasks_json(available_tasks))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
            }
        """)
        title_layout.addWidget(export_btn)
        
        layout.addLayout(title_layout)
        
        from .filter_dialog import TagFilterWidget
        self.pool_filter_widget = TagFilterWidget(self.db)
        self.pool_filter_widget.filter_changed.connect(self._on_pool_filter_changed)
        layout.addWidget(self.pool_filter_widget)
        
        self.pool_task_list = QListWidget()
        self.pool_task_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.pool_task_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
        """)
        self._populate_pool_list(available_tasks)
        layout.addWidget(self.pool_task_list)
        
        btn_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️ 编辑选中")
        edit_btn.clicked.connect(self._edit_selected_task)
        btn_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️ 删除选中")
        delete_btn.clicked.connect(self._delete_selected_tasks)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
            }
        """)
        btn_layout.addWidget(delete_btn)
        
        add_tag_btn = QPushButton("🏷️ 批量添加标签")
        add_tag_btn.clicked.connect(self._batch_add_tag)
        btn_layout.addWidget(add_tag_btn)
        
        clear_tag_btn = QPushButton("🗑️ 批量清除标签")
        clear_tag_btn.clicked.connect(self._batch_clear_tags)
        btn_layout.addWidget(clear_tag_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _populate_pool_list(self, tasks):
        self.pool_task_list.clear()
        for task in tasks:
            tags = task.get('tags', [])
            tags_str = ""
            if tags:
                tags_str = " | 🏷️ " + ", ".join(tags[:2])
                if len(tags) > 2:
                    tags_str += f"...(+{len(tags)-2})"
            
            repeat_info = ""
            if task.get('repeat_type') == 'daily':
                repeat_info = " | 🔄 每日"
            elif task.get('repeat_type') == 'weekly':
                repeat_info = " | 📅 每周"
            elif task.get('repeat_type') == 'accumulation':
                repeat_info = " | 📚 复习"
            
            item_text = f"{task['name']} | ⏱️ {task.get('estimated_time', 0)}分钟{repeat_info}{tags_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, task['id'])
            self.pool_task_list.addItem(item)
    
    def _edit_selected_task(self):
        selected_items = self.pool_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要编辑的任务！")
            return
        
        if len(selected_items) > 1:
            QMessageBox.warning(self, "提示", "一次只能编辑一个任务！")
            return
        
        task_id = selected_items[0].data(Qt.UserRole)
        task_data = self.db.get_task_by_id(task_id)
        
        if not task_data:
            QMessageBox.warning(self, "提示", "任务不存在！")
            return
        
        from .main_window import TaskEditDialog
        dialog = TaskEditDialog(self, db=self.db, task=Task.from_dict(task_data))
        if dialog.exec():
            updated_task = dialog.get_task()
            task_dict = {
                'name': updated_task.name,
                'category': updated_task.category,
                'description': updated_task.description,
                'estimated_time': updated_task.estimated_time,
                'repeat_type': updated_task.repeat_type,
                'difficulty': updated_task.difficulty,
                'priority': updated_task.priority
            }
            self.db.update_task(task_id, **task_dict)
            if updated_task.tags:
                self.db.set_task_tags(task_id, updated_task.tags)
            else:
                self.db.set_task_tags(task_id, [])
            QMessageBox.information(self, "成功", "✅ 任务编辑成功！")
            self.all_pool_tasks = self.db.get_available_tasks_for_gacha()
            self._apply_pool_filter()
    
    def _delete_selected_tasks(self):
        selected_items = self.pool_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要删除的任务！")
            return
        
        count = len(selected_items)
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除选中的 {count} 个任务吗？"
        )
        if reply == QMessageBox.Yes:
            for item in selected_items:
                task_id = item.data(Qt.UserRole)
                self.db.delete_task(task_id)
            QMessageBox.information(self, "成功", f"✅ 已删除 {count} 个任务！")
            self.all_pool_tasks = self.db.get_available_tasks_for_gacha()
            self._apply_pool_filter()
    
    def _batch_add_tag(self):
        selected_items = self.pool_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择任务！")
            return
        
        from PySide6.QtWidgets import QInputDialog
        tag_name, ok = QInputDialog.getText(self, "添加标签", "请输入标签名称：")
        if ok and tag_name.strip():
            tag_name = tag_name.strip()
            for item in selected_items:
                task_id = item.data(Qt.UserRole)
                task_data = self.db.get_task_by_id(task_id)
                if task_data:
                    existing_tags = task_data.get('tags', [])
                    if tag_name not in existing_tags:
                        existing_tags.append(tag_name)
                        self.db.set_task_tags(task_id, existing_tags)
            QMessageBox.information(self, "成功", f"✅ 已为 {len(selected_items)} 个任务添加标签「{tag_name}」！")
            self.all_pool_tasks = self.db.get_available_tasks_for_gacha()
            self._apply_pool_filter()
    
    def _batch_clear_tags(self):
        selected_items = self.pool_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择任务！")
            return
        
        reply = QMessageBox.question(
            self, 
            "确认清除标签", 
            f"确定要清除选中的 {len(selected_items)} 个任务的所有标签吗？"
        )
        if reply == QMessageBox.Yes:
            for item in selected_items:
                task_id = item.data(Qt.UserRole)
                self.db.set_task_tags(task_id, [])
            QMessageBox.information(self, "成功", f"✅ 已清除 {len(selected_items)} 个任务的标签！")
            self.all_pool_tasks = self.db.get_available_tasks_for_gacha()
            self._apply_pool_filter()
    
    def _import_tasks_json(self, parent_dialog):
        import json
        import os
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择JSON文件", 
            "", 
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
            
            if not isinstance(tasks_data, list):
                QMessageBox.warning(self, "错误", "JSON文件格式不正确！应为任务数组。")
                return
            
            imported_count = 0
            imported_tags = set()
            
            for task_data in tasks_data:
                if isinstance(task_data, dict) and 'name' in task_data:
                    task = Task(
                        name=task_data.get('name', ''),
                        description=task_data.get('description', ''),
                        category=task_data.get('category', 'daily'),
                        estimated_time=task_data.get('estimated_time', 25),
                        repeat_type=task_data.get('repeat_type', 'single'),
                        difficulty=task_data.get('difficulty', 1),
                        priority=task_data.get('priority', 5),
                        task_type=task_data.get('task_type', 'other'),
                        resistance=task_data.get('resistance', 'medium'),
                        energy_required=task_data.get('energy_required', 'medium'),
                        preferred_time=task_data.get('preferred_time'),
                        deadline=task_data.get('deadline'),
                        tags=task_data.get('tags', [])
                    )
                    task_id = self.db.add_task(task)
                    if task.tags:
                        self.db.set_task_tags(task_id, task.tags)
                        imported_tags.update(task.tags)
                    imported_count += 1
            
            QMessageBox.information(self, "成功", f"✅ 成功导入 {imported_count} 个任务！\n📋 涉及 {len(imported_tags)} 个标签。")
            self.all_pool_tasks = self.db.get_available_tasks_for_gacha()
            self._apply_pool_filter()
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导入失败：{str(e)}")
    
    def _export_tasks_json(self, tasks):
        import json
        import os
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存JSON文件", 
            "", 
            "JSON文件 (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            tasks_list = []
            for task in tasks:
                tasks_list.append({
                    'name': task.get('name', ''),
                    'description': task.get('description', ''),
                    'category': task.get('category', 'daily'),
                    'estimated_time': task.get('estimated_time', 25),
                    'repeat_type': task.get('repeat_type', 'single'),
                    'difficulty': task.get('difficulty', 1),
                    'priority': task.get('priority', 5),
                    'task_type': task.get('task_type', 'other'),
                    'resistance': task.get('resistance', 'medium'),
                    'energy_required': task.get('energy_required', 'medium'),
                    'preferred_time': task.get('preferred_time'),
                    'deadline': task.get('deadline'),
                    'tags': task.get('tags', [])
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_list, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "成功", f"✅ 已导出 {len(tasks_list)} 个任务！")
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"导出失败：{str(e)}")
    
    def _get_all_tags(self):
        tags = self.db.get_all_tags()
        return tags
    
    def _on_pool_filter_changed(self, filter_dict):
        self.current_pool_filter = filter_dict
        self._apply_pool_filter()
    
    def _apply_pool_filter(self):
        if not hasattr(self, 'current_pool_filter'):
            self.current_pool_filter = {
                'tags': [],
                'mode': 'union',
                'repeat_types': [],
                'show_no_tags': False
            }
        
        filter_dict = self.current_pool_filter
        filtered_tasks = []
        
        for task in self.all_pool_tasks:
            task_tags = task.get('tags', [])
            task_repeat = task.get('repeat_type', 'single')
            
            if not self._task_matches_filter(task, filter_dict):
                continue
            
            filtered_tasks.append(task)
        
        self._populate_pool_list(filtered_tasks)
    
    def _task_matches_filter(self, task, filter_dict):
        task_tags = task.get('tags', [])
        task_repeat = task.get('repeat_type', 'single')
        tags = filter_dict.get('tags', [])
        mode = filter_dict.get('mode', 'union')
        repeat_types = filter_dict.get('repeat_types', [])
        show_no_tags = filter_dict.get('show_no_tags', False)
        
        if repeat_types and task_repeat not in repeat_types:
            return False
        
        if not tags and not show_no_tags:
            return True
        
        if not tags and show_no_tags:
            return len(task_tags) == 0
        
        if tags:
            if mode == 'union':
                if any(t in task_tags for t in tags):
                    return True
                if show_no_tags and len(task_tags) == 0:
                    return True
                return False
            else:
                if all(t in task_tags for t in tags):
                    return True
                if show_no_tags and len(task_tags) == 0 and len(tags) == 0:
                    return True
                return False
        
        return True
    
    def _open_discard_pile(self):
        tasks = self.db.get_discard_pile_tasks()
        
        if not tasks:
            QMessageBox.information(self, "弃牌堆", "弃牌堆为空！")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("🗑️ 弃牌堆")
        dialog.setMinimumSize(700, 550)
        
        layout = QVBoxLayout(dialog)
        
        title_layout = QHBoxLayout()
        title = QLabel(f"弃牌堆中有 {len(tasks)} 个任务")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        from .filter_dialog import TagFilterWidget
        self.discard_filter_widget = TagFilterWidget(self.db)
        self.discard_filter_widget.filter_changed.connect(self._on_discard_filter_changed)
        layout.addWidget(self.discard_filter_widget)
        
        self.all_discard_tasks = tasks
        self.discard_task_list = QListWidget()
        self.discard_task_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.discard_task_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #e8f4f8;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
        """)
        self._populate_discard_list(tasks)
        layout.addWidget(self.discard_task_list)
        
        btn_layout = QHBoxLayout()
        
        self.pick_btn = QPushButton("🎴 抓回抽牌堆")
        self.pick_btn.clicked.connect(self._pick_from_discard)
        btn_layout.addWidget(self.pick_btn)
        
        reset_all_btn = QPushButton("🔄 重置全部")
        reset_all_btn.clicked.connect(self._reset_all_discard)
        btn_layout.addWidget(reset_all_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _populate_discard_list(self, tasks):
        self.discard_task_list.clear()
        for task in tasks:
            tags = task.get('tags', [])
            tags_str = ""
            if tags:
                tags_str = " | 🏷️ " + ", ".join(tags[:2])
                if len(tags) > 2:
                    tags_str += f"...(+{len(tags)-2})"
            
            repeat_info = ""
            if task.get('repeat_type') == 'daily':
                repeat_info = " | 🔄 每日"
            elif task.get('repeat_type') == 'weekly':
                repeat_info = " | 📅 每周"
            elif task.get('repeat_type') == 'accumulation':
                repeat_info = " | 📚 复习"
            
            item_text = f"{task['name']} | ⏱️ {task.get('estimated_time', 0)}分钟{repeat_info}{tags_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, task['id'])
            self.discard_task_list.addItem(item)
    
    def _on_discard_filter_changed(self, filter_dict):
        self.current_discard_filter = filter_dict
        self._apply_discard_filter()
    
    def _apply_discard_filter(self):
        if not hasattr(self, 'current_discard_filter'):
            self.current_discard_filter = {
                'tags': [],
                'mode': 'union',
                'repeat_types': [],
                'show_no_tags': False
            }
        
        filter_dict = self.current_discard_filter
        filtered_tasks = []
        
        for task in self.all_discard_tasks:
            if self._task_matches_filter(task, filter_dict):
                filtered_tasks.append(task)
        
        self._populate_discard_list(filtered_tasks)
    
    def _pick_from_discard(self):
        selected_items = self.discard_task_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "提示", "请先选择要抓回的任务！")
            return
        
        for item in selected_items:
            task_id = item.data(Qt.UserRole)
            self.db.remove_from_discard_pile(task_id)
        
        QMessageBox.information(self, "成功", "✅ 任务已抓回抽牌堆！")
        self.all_discard_tasks = self.db.get_discard_pile_tasks()
        self._apply_discard_filter()

    def _reset_all_discard(self):
        reply = QMessageBox.question(
            self, 
            "确认重置", 
            "确定要将所有任务从弃牌堆抓回吗？"
        )
        if reply == QMessageBox.Yes:
            self.db.reset_all_discard_pile()
            QMessageBox.information(self, "成功", "✅ 弃牌堆已全部重置！")

    def _random_pick(self):
        from ..services.task_service import TaskService
        
        task_service = TaskService(self.db)
        task = task_service.get_random_task()
        if task:
            self._select_task(task)
        else:
            QMessageBox.information(self, "提示", "暂无可用任务，请先添加任务！")