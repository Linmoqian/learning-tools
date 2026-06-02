"""
晨间评估对话框
包含两级动态诊断协议
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QComboBox, QDialogButtonBox, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont, QPalette, QColor

from core.database import DatabaseManager
from config.constants import SLEEP_QUALITY_MAPPING, TIME_SLOTS
from config.config_manager import get_config_manager


class MorningAssessmentDialog(QDialog):
    """晨间评估对话框"""

    assessment_completed = pyqtSignal(dict)  # 评估完成信号

    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager
        self.current_level = 1
        self.assessment_data = {}
        self.recalibration_timer = None

        # 获取配置管理器
        self.config_manager = get_config_manager()

        self.setup_ui()

    def setup_ui(self):
        """设置对话框界面"""
        self.setWindowTitle("StateOS - 晨间评估")
        self.setModal(True)
        self.setFixedSize(700, 650)  # 增加高度以适应更多时间段

        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 标题
        title = QLabel("🌅 晨间状态评估")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 子标题
        self.subtitle = QLabel("第一级评估：宏观日程与初诊")
        self.subtitle.setFont(QFont("Microsoft YaHei", 14))
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.subtitle)

        # 创建评估区域
        self.assessment_widget = QGroupBox()
        self.assessment_widget.setStyleSheet("""
            QGroupBox {
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 20px;
                margin-top: 10px;
            }
        """)

        self.assessment_layout = QVBoxLayout(self.assessment_widget)
        self.create_level1_assessment()

        main_layout.addWidget(self.assessment_widget)

        # 进度条（用于30分钟倒计时）
        self.progress_label = QLabel("")
        self.progress_label.setFont(QFont("Microsoft YaHei", 10))
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setVisible(False)
        main_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 30 * 60)  # 30分钟，以秒为单位
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.next_button = QPushButton("下一步")
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 12px 30px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.next_button.clicked.connect(self.handle_next)
        button_layout.addWidget(self.next_button)

        self.skip_button = QPushButton("跳过评估")
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.skip_button.clicked.connect(self.skip_assessment)
        button_layout.addWidget(self.skip_button)

        main_layout.addLayout(button_layout)

    def get_course_options(self) -> list:
        """获取课程选项（从配置文件）"""
        return self.config_manager.get_course_options()

    def create_level1_assessment(self):
        """创建第一级评估界面"""
        # 清空现有内容
        self.clear_assessment_layout()

        # 获取课程选项
        course_options = self.get_course_options()

        # 日程选择
        schedule_group = QGroupBox("📅 今日日程安排")
        schedule_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }
        """)

        schedule_layout = QGridLayout(schedule_group)
        schedule_layout.setSpacing(8)  # 减小间距

        # 创建5个时间段的组合框
        time_slots = [
            ("morning_1", "上午第一时段 (08:00-10:00):", "morning1_combo"),
            ("morning_2", "上午第二时段 (10:00-12:00):", "morning2_combo"),
            ("afternoon_1", "下午第一时段 (14:00-16:00):", "afternoon1_combo"),
            ("afternoon_2", "下午第二时段 (16:00-18:00):", "afternoon2_combo"),
            ("evening", "晚间时段 (19:00-21:00):", "evening_combo")
        ]

        for i, (slot_key, slot_label, combo_name) in enumerate(time_slots):
            # 标签
            label = QLabel(slot_label)
            label.setFont(QFont("Microsoft YaHei", 10))
            schedule_layout.addWidget(label, i, 0)

            # 组合框
            combo = QComboBox()
            combo.addItems(course_options)
            combo.setCurrentText("无安排")
            combo.setFont(QFont("Microsoft YaHei", 10))
            combo.setProperty("time_slot", slot_key)  # 存储时间段标识

            # 保存到实例变量
            setattr(self, combo_name, combo)

            schedule_layout.addWidget(combo, i, 1)

        self.assessment_layout.addWidget(schedule_group)

        # 状态初诊
        state_group = QGroupBox("💤 睡眠质量与初诊")
        state_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                margin-top: 15px;
            }
        """)

        state_layout = QVBoxLayout(state_group)

        self.sleep_radio_group = QButtonGroup(self)
        sleep_options = list(SLEEP_QUALITY_MAPPING.keys())

        for i, option in enumerate(sleep_options):
            radio = QRadioButton(option)
            radio.setFont(QFont("Microsoft YaHei", 10))
            radio.setStyleSheet("padding: 8px;")
            self.sleep_radio_group.addButton(radio, i)
            state_layout.addWidget(radio)

        # 默认选择第一个选项
        if sleep_options:
            self.sleep_radio_group.button(0).setChecked(True)

        self.assessment_layout.addWidget(state_group)

        # 说明文字
        note = QLabel("💡 提示：如果选择后两项（'困倦'或'头痛/头晕'），30分钟后会进行再校准")
        note.setFont(QFont("Microsoft YaHei", 9))
        note.setStyleSheet("color: #7f8c8d; padding: 10px 0;")
        note.setWordWrap(True)
        self.assessment_layout.addWidget(note)

        # 添加配置提示
        config_note = QLabel("📝 提示：可在 config/user_config.yml 中自定义课程选项")
        config_note.setFont(QFont("Microsoft YaHei", 9))
        config_note.setStyleSheet("color: #3498db; padding: 5px; background-color: #ecf0f1; border-radius: 4px;")
        config_note.setWordWrap(True)
        self.assessment_layout.addWidget(config_note)

    def create_level2_assessment(self):
        """创建第二级评估界面"""
        # 清空现有内容
        self.clear_assessment_layout()

        self.subtitle.setText("第二级评估：行动后再校准")

        # 问题描述
        question_label = QLabel("❓ 经过晨间惯例（如饮水、早餐、光照）后，当前状态是否好转？")
        question_label.setFont(QFont("Microsoft YaHei", 12))
        question_label.setWordWrap(True)
        question_label.setStyleSheet("padding-bottom: 15px;")
        self.assessment_layout.addWidget(question_label)

        # 选项
        options_group = QGroupBox("请选择:")
        options_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }
        """)

        options_layout = QVBoxLayout(options_group)

        self.improvement_radio_group = QButtonGroup(self)
        improvement_options = [
            "明显好转，可以开始",
            "略有改善，但需谨慎",
            "没有变化，仍感不适"
        ]

        for i, option in enumerate(improvement_options):
            radio = QRadioButton(option)
            radio.setFont(QFont("Microsoft YaHei", 10))
            radio.setStyleSheet("padding: 8px;")
            self.improvement_radio_group.addButton(radio, i)
            options_layout.addWidget(radio)

        # 默认选择第一个选项
        if improvement_options:
            self.improvement_radio_group.button(0).setChecked(True)

        self.assessment_layout.addWidget(options_group)

        # 说明文字
        note = QLabel("💡 提示：根据您的选择，系统会相应调整初始状态值")
        note.setFont(QFont("Microsoft YaHei", 9))
        note.setStyleSheet("color: #7f8c8d; padding: 10px 0;")
        self.assessment_layout.addWidget(note)

        # 更新按钮文本
        self.next_button.setText("完成评估")
        self.next_button.setEnabled(True)

        # 隐藏跳过按钮
        self.skip_button.setVisible(False)

    def clear_assessment_layout(self):
        """清空评估布局"""
        while self.assessment_layout.count():
            item = self.assessment_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def handle_next(self):
        """处理下一步按钮"""
        if self.current_level == 1:
            # 验证第一级评估
            if not self.validate_level1():
                return

            # 保存第一级评估数据
            self.save_level1_data()

            # 检查是否需要第二级评估
            selected_option = self.get_selected_sleep_quality()
            needs_recalibration = selected_option in ["没睡好，感到困倦", "没睡好，头痛/头晕"]

            if needs_recalibration:
                self.start_recalibration_timer()
            else:
                self.complete_assessment()

        elif self.current_level == 2:
            # 完成第二级评估
            if not self.validate_level2():
                return

            self.save_level2_data()
            self.complete_assessment()

    def validate_level1(self) -> bool:
        """验证第一级评估数据"""
        # 检查是否选择了睡眠质量
        selected_button = self.sleep_radio_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "验证失败", "请选择睡眠质量选项")
            return False

        return True

    def validate_level2(self) -> bool:
        """验证第二级评估数据"""
        # 检查是否选择了改善程度
        selected_button = self.improvement_radio_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "验证失败", "请选择状态改善程度")
            return False

        return True

    def get_selected_sleep_quality(self) -> str:
        """获取选择的睡眠质量"""
        selected_button = self.sleep_radio_group.checkedButton()
        return selected_button.text() if selected_button else ""

    def save_level1_data(self):
        """保存第一级评估数据"""
        selected_quality = self.get_selected_sleep_quality()

        self.assessment_data.update({
            'date': self.db.get_today_date(),
            'sleep_quality_initial': selected_quality,
            'course_morning_1': self.morning1_combo.currentText(),
            'course_morning_2': self.morning2_combo.currentText(),
            'course_afternoon_1': self.afternoon1_combo.currentText(),
            'course_afternoon_2': self.afternoon2_combo.currentText(),
            'course_evening': self.evening_combo.currentText(),
            'energy_initial': SLEEP_QUALITY_MAPPING[selected_quality]['energy'],
            'thirst_initial': SLEEP_QUALITY_MAPPING[selected_quality]['thirst'],
            'hunger_initial': SLEEP_QUALITY_MAPPING[selected_quality]['hunger']
        })

    def save_level2_data(self):
        """保存第二级评估数据"""
        selected_button = self.improvement_radio_group.checkedButton()
        if selected_button:
            self.assessment_data['sleep_quality_adjusted'] = selected_button.text()

    def start_recalibration_timer(self):
        """启动30分钟再校准计时器"""
        # 禁用下一步按钮
        self.next_button.setEnabled(False)
        self.skip_button.setEnabled(False)

        # 显示倒计时
        self.progress_label.setVisible(True)
        self.progress_bar.setVisible(True)

        # 更新标题
        self.subtitle.setText("⏳ 30分钟后再校准")

        # 显示提示信息
        info_label = QLabel(
            "✅ 第一级评估已完成\n\n"
            "⏰ 系统将在30分钟后弹出再校准对话框\n"
            "☕ 在此期间，请进行晨间惯例活动：\n"
            "   • 饮水（300-500ml）\n"
            "   • 早餐（适量蛋白质）\n"
            "   • 光照（自然光15分钟）\n"
            "   • 轻度活动（5-10分钟）\n\n"
            "💡 您可以最小化此窗口，计时器会在后台运行"
        )
        info_label.setFont(QFont("Microsoft YaHei", 10))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("padding: 15px;")

        self.clear_assessment_layout()
        self.assessment_layout.addWidget(info_label)

        # 启动倒计时
        self.seconds_remaining = 30 * 60  # 30分钟
        self.progress_bar.setValue(0)

        self.recalibration_timer = QTimer()
        self.recalibration_timer.timeout.connect(self.update_countdown)
        self.recalibration_timer.start(1000)  # 每秒更新一次

        # 30分钟后切换到第二级评估
        self.level2_timer = QTimer()
        self.level2_timer.setSingleShot(True)
        self.level2_timer.timeout.connect(self.show_level2_assessment)
        self.level2_timer.start(30 * 60 * 1000)  # 30分钟

        self.current_level = 1.5  # 中间状态

    def update_countdown(self):
        """更新倒计时显示"""
        self.seconds_remaining -= 1

        # 更新进度条
        self.progress_bar.setValue(30 * 60 - self.seconds_remaining)

        # 更新标签
        minutes = self.seconds_remaining // 60
        seconds = self.seconds_remaining % 60
        self.progress_label.setText(f"倒计时: {minutes:02d}:{seconds:02d}")

        if self.seconds_remaining <= 0:
            self.recalibration_timer.stop()
            self.progress_label.setText("时间到！请进行再评估")

    def show_level2_assessment(self):
        """显示第二级评估"""
        # 停止倒计时
        if self.recalibration_timer:
            self.recalibration_timer.stop()

        # 隐藏倒计时显示
        self.progress_label.setVisible(False)
        self.progress_bar.setVisible(False)

        # 切换到第二级评估
        self.current_level = 2
        self.create_level2_assessment()

        # 恢复按钮
        self.next_button.setEnabled(True)

        # 显示提示
        QMessageBox.information(
            self,
            "再校准时间到",
            "30分钟已过，请根据您的实际状态进行再评估。"
        )

    def complete_assessment(self):
        """完成评估流程"""
        try:
            # 计算最终状态
            from config.constants import SLEEP_QUALITY_MAPPING, SECOND_LEVEL_ADJUSTMENTS

            sleep_quality = self.assessment_data['sleep_quality_initial']
            initial_state = SLEEP_QUALITY_MAPPING[sleep_quality].copy()

            # 应用第二级评估调整
            if 'sleep_quality_adjusted' in self.assessment_data:
                adjustment = self.assessment_data['sleep_quality_adjusted']
                energy_adjustment = SECOND_LEVEL_ADJUSTMENTS.get(adjustment, 0)

                if adjustment == "没有变化，仍感不适":
                    self.assessment_data['low_power_mode'] = True

                # 调整精力值
                initial_state['energy'] = min(100, initial_state['energy'] + energy_adjustment)

            # 保存评估数据到数据库
            self.assessment_data.update({
                'energy_initial': initial_state['energy'],
                'thirst_initial': initial_state['thirst'],
                'hunger_initial': initial_state['hunger']
            })

            self.db.save_daily_checkin(self.assessment_data)

            # 发出完成信号
            self.assessment_completed.emit(initial_state)
            self.accept()

            self.show_success_message(initial_state)

        except Exception as e:
            QMessageBox.critical(self, "评估失败", f"评估过程出现错误:\n{str(e)}")
            self.reject()

    def show_success_message(self, initial_state: dict):
        """显示成功消息"""
        message = (
            f"✅ 晨间评估完成！\n\n"
            f"📊 您的初始状态已设定：\n"
            f"   • 精力值: {initial_state['energy']}%\n"
            f"   • 口渴值: {initial_state['thirst']}%\n"
            f"   • 饥饿值: {initial_state['hunger']}%\n\n"
            f"🚀 开始您的高效一天吧！"
        )

        QMessageBox.information(self, "评估完成", message)

    def skip_assessment(self):
        """跳过评估"""
        reply = QMessageBox.question(
            self,
            "跳过评估",
            "确定要跳过晨间评估吗？\n系统将使用默认状态值（75%）。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # 使用默认状态值
            default_state = {'energy': 75, 'thirst': 75, 'hunger': 75}
            self.assessment_completed.emit(default_state)
            self.reject()

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.current_level == 1.5:  # 正在倒计时中
            reply = QMessageBox.question(
                self,
                "确认关闭",
                "倒计时仍在进行中，关闭窗口将取消再校准。\n确定要关闭吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # 停止计时器
                if self.recalibration_timer:
                    self.recalibration_timer.stop()
                if hasattr(self, 'level2_timer'):
                    self.level2_timer.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
