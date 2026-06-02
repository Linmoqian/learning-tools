"""
认知过载对话框
用于处理任务分解和清空
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QMessageBox, QGroupBox, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class OverloadDialog(QDialog):
    """认知过载对话框"""

    tasks_decomposed = pyqtSignal(list)  # 任务分解完成信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.setup_ui()

    def setup_ui(self):
        """设置对话框界面"""
        self.setWindowTitle("🧠 认知过载处理")
        self.setModal(True)
        self.setMinimumSize(600, 500)

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("认知过载 - 任务分解")
        title_font = QFont("Microsoft YaHei", 16, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # 说明文字
        description = QLabel(
            "💡 感到认知过载？让我们将复杂的任务拆解成最小可执行步骤。\n"
            "输入让您感到压力的任务，然后逐步分解它。"
        )
        description.setFont(QFont("Microsoft YaHei", 10))
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        main_layout.addWidget(description)

        # 输入区域
        input_group = QGroupBox("📝 输入主要任务")
        input_group.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        input_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #f39c12;
                border-radius: 6px;
                padding-top: 10px;
                margin-top: 5px;
            }
        """)

        input_layout = QVBoxLayout(input_group)

        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("例如：完成数学作业、准备会议报告、整理房间...")
        self.task_input.setFont(QFont("Microsoft YaHei", 10))
        self.task_input.setStyleSheet("padding: 8px; border: 1px solid #bdc3c7; border-radius: 4px;")
        input_layout.addWidget(self.task_input)

        add_button = QPushButton("添加到分解列表")
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #d68910;
            }
        """)
        add_button.clicked.connect(self.add_main_task)
        input_layout.addWidget(add_button)

        main_layout.addWidget(input_group)

        # 任务列表区域
        tasks_group = QGroupBox("📋 待分解任务列表")
        tasks_group.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        tasks_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 6px;
                padding-top: 10px;
                margin-top: 10px;
            }
        """)

        tasks_layout = QVBoxLayout(tasks_group)

        self.tasks_list = QListWidget()
        self.tasks_list.setFont(QFont("Microsoft YaHei", 10))
        self.tasks_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                margin: 2px;
                border-radius: 3px;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        self.tasks_list.setAlternatingRowColors(True)
        tasks_layout.addWidget(self.tasks_list)

        # 列表操作按钮
        list_buttons_layout = QHBoxLayout()

        remove_button = QPushButton("移除选中")
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        remove_button.clicked.connect(self.remove_selected_task)
        list_buttons_layout.addWidget(remove_button)

        clear_button = QPushButton("清空列表")
        clear_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        clear_button.clicked.connect(self.clear_tasks_list)
        list_buttons_layout.addWidget(clear_button)

        tasks_layout.addLayout(list_buttons_layout)

        main_layout.addWidget(tasks_group)

        # 分解区域
        decompose_group = QGroupBox("🔨 任务分解")
        decompose_group.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        decompose_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #2ecc71;
                border-radius: 6px;
                padding-top: 10px;
                margin-top: 10px;
            }
        """)

        decompose_layout = QVBoxLayout(decompose_group)

        decompose_instructions = QLabel(
            "选中一个任务，然后输入分解步骤（每行一个步骤）：\n"
            "• 每个步骤应该是具体的、可执行的\n"
            "• 每个步骤应该在5-30分钟内完成\n"
            "• 使用动词开头，如：打开、写下、查找、整理"
        )
        decompose_instructions.setFont(QFont("Microsoft YaHei", 9))
        decompose_instructions.setWordWrap(True)
        decompose_instructions.setStyleSheet("color: #7f8c8d; padding: 5px;")
        decompose_layout.addWidget(decompose_instructions)

        self.decompose_input = QTextEdit()
        self.decompose_input.setPlaceholderText(
            "输入分解步骤，每行一个...\n例如：\n1. 打开数学课本第45页\n2. 阅读例题1和例题2\n3. 完成练习1的前3题\n4. 检查答案并标记疑问")
        self.decompose_input.setFont(QFont("Microsoft YaHei", 10))
        self.decompose_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 8px;
                min-height: 120px;
            }
        """)
        decompose_layout.addWidget(self.decompose_input)

        decompose_button = QPushButton("分解选中任务")
        decompose_button.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        decompose_button.clicked.connect(self.decompose_selected_task)
        decompose_layout.addWidget(decompose_button)

        main_layout.addWidget(decompose_group)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.finish_button = QPushButton("✅ 完成并清空任务")
        self.finish_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.finish_button.clicked.connect(self.finish_decomposition)
        self.finish_button.setEnabled(False)
        button_layout.addWidget(self.finish_button)

        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        main_layout.addLayout(button_layout)

        # 初始化状态
        self.update_finish_button()

    def add_main_task(self):
        """添加主要任务到列表"""
        task_text = self.task_input.text().strip()
        if not task_text:
            QMessageBox.warning(self, "输入错误", "请输入任务内容")
            return

        # 添加到列表
        item = QListWidgetItem(f"📌 {task_text}")
        item.setData(Qt.ItemDataRole.UserRole, task_text)
        self.tasks_list.addItem(item)

        # 清空输入框
        self.task_input.clear()

        # 更新按钮状态
        self.update_finish_button()

    def remove_selected_task(self):
        """移除选中的任务"""
        current_row = self.tasks_list.currentRow()
        if current_row >= 0:
            self.tasks_list.takeItem(current_row)
            self.update_finish_button()

    def clear_tasks_list(self):
        """清空任务列表"""
        if self.tasks_list.count() > 0:
            reply = QMessageBox.question(
                self,
                "确认清空",
                "确定要清空所有任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.tasks_list.clear()
                self.update_finish_button()

    def decompose_selected_task(self):
        """分解选中的任务"""
        current_item = self.tasks_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "选择错误", "请先选择一个任务进行分解")
            return

        steps_text = self.decompose_input.toPlainText().strip()
        if not steps_text:
            QMessageBox.warning(self, "输入错误", "请输入分解步骤")
            return

        # 获取步骤列表
        steps = [step.strip() for step in steps_text.split('\n') if step.strip()]

        if not steps:
            QMessageBox.warning(self, "输入错误", "请输入有效的分解步骤")
            return

        # 更新任务项，显示已分解
        task_text = current_item.data(Qt.ItemDataRole.UserRole)
        step_count = len(steps)
        current_item.setText(f"✅ {task_text} (已分解为{step_count}个步骤)")

        # 存储分解结果
        current_item.setData(Qt.ItemDataRole.UserRole + 1, steps)

        # 清空分解输入框
        self.decompose_input.clear()

        # 显示成功消息
        QMessageBox.information(
            self,
            "分解成功",
            f"任务已成功分解为 {step_count} 个步骤。"
        )

    def finish_decomposition(self):
        """完成分解过程"""
        if self.tasks_list.count() == 0:
            QMessageBox.warning(self, "无任务", "没有需要处理的任务")
            return

        # 收集所有分解的步骤
        all_steps = []

        for i in range(self.tasks_list.count()):
            item = self.tasks_list.item(i)
            steps = item.data(Qt.ItemDataRole.UserRole + 1)
            if steps:
                all_steps.extend(steps)

        if not all_steps:
            QMessageBox.warning(self, "无分解步骤", "请至少分解一个任务")
            return

        # 发送信号
        self.tasks_decomposed.emit(all_steps)

        # 显示总结
        reply = QMessageBox.information(
            self,
            "分解完成",
            f"✅ 已成功将任务分解为 {len(all_steps)} 个可执行步骤。\n\n"
            f"是否要查看分解结果？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.show_decomposition_summary(all_steps)

        self.accept()

    def show_decomposition_summary(self, steps):
        """显示分解总结"""
        summary_dialog = QDialog(self)
        summary_dialog.setWindowTitle("任务分解总结")
        summary_dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout(summary_dialog)

        title = QLabel("📋 您的可执行步骤清单")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        for i, step in enumerate(steps, 1):
            step_label = QLabel(f"{i}. {step}")
            step_label.setFont(QFont("Microsoft YaHei", 10))
            step_label.setWordWrap(True)
            step_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    margin: 2px;
                    border: 1px solid #ecf0f1;
                    border-radius: 4px;
                    background-color: #f8f9fa;
                }
            """)
            scroll_layout.addWidget(step_label)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(summary_dialog.accept)
        layout.addWidget(close_button)

        summary_dialog.exec()

    def update_finish_button(self):
        """更新完成按钮状态"""
        has_tasks = self.tasks_list.count() > 0
        self.finish_button.setEnabled(has_tasks)

    def get_tasks(self):
        """获取所有分解的步骤"""
        all_steps = []

        for i in range(self.tasks_list.count()):
            item = self.tasks_list.item(i)
            steps = item.data(Qt.ItemDataRole.UserRole + 1)
            if steps:
                all_steps.extend(steps)

        return all_steps
