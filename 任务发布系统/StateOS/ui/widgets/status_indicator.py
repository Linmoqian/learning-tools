"""
状态指示器组件
自定义状态显示组件
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen
from typing import Dict, Any


class StatusIndicator(QWidget):
    """状态指示器组件"""

    value_changed = pyqtSignal(str, int)  # 属性名, 新值

    def __init__(self, attribute_name: str, display_name: str,
                 color: str = "#3498db", parent=None):
        super().__init__(parent)
        self.attribute_name = attribute_name
        self.display_name = display_name
        self.color = color
        self.current_value = 50
        self.min_value = 0
        self.max_value = 100

        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 标签和值显示
        info_layout = QHBoxLayout()

        self.name_label = QLabel(self.display_name)
        self.name_label.setFont(QFont("Microsoft YaHei", 11))
        self.name_label.setStyleSheet("color: #2c3e50;")
        info_layout.addWidget(self.name_label)

        info_layout.addStretch()

        self.value_label = QLabel("50%")
        self.value_label.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {self.color};")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.addWidget(self.value_label)

        main_layout.addLayout(info_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(self.min_value, self.max_value)
        self.progress_bar.setValue(self.current_value)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v%")

        # 设置进度条样式
        self.update_progress_style()

        main_layout.addWidget(self.progress_bar)

        # 设置组件最小尺寸
        self.setMinimumHeight(70)

    def update_progress_style(self):
        """更新进度条样式"""
        style = f"""
            QProgressBar {{
                height: 20px;
                text-align: center;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {self.color};
                border-radius: 5px;
            }}
        """
        self.progress_bar.setStyleSheet(style)

    def set_value(self, value: int):
        """设置当前值"""
        # 确保值在范围内
        clamped_value = max(self.min_value, min(self.max_value, value))

        if clamped_value != self.current_value:
            self.current_value = clamped_value
            self.progress_bar.setValue(self.current_value)
            self.value_label.setText(f"{self.current_value}%")

            # 根据值改变颜色
            self.update_color_based_on_value()

            # 发出值改变信号
            self.value_changed.emit(self.attribute_name, self.current_value)

    def get_value(self) -> int:
        """获取当前值"""
        return self.current_value

    def update_color_based_on_value(self):
        """根据值更新颜色"""
        if self.current_value < 30:
            # 危险值 - 红色
            new_color = "#e74c3c"
        elif self.current_value < 60:
            # 警告值 - 橙色
            new_color = "#e67e22"
        elif self.current_value < 80:
            # 正常值 - 蓝色
            new_color = "#3498db"
        else:
            # 良好值 - 绿色
            new_color = "#2ecc71"

        if new_color != self.color:
            self.color = new_color
            self.value_label.setStyleSheet(f"color: {self.color};")
            self.update_progress_style()

    def set_range(self, min_val: int, max_val: int):
        """设置值范围"""
        self.min_value = min_val
        self.max_value = max_val
        self.progress_bar.setRange(min_val, max_val)

    def set_display_name(self, name: str):
        """设置显示名称"""
        self.display_name = name
        self.name_label.setText(name)

    def set_color(self, color: str):
        """设置颜色"""
        self.color = color
        self.value_label.setStyleSheet(f"color: {color};")
        self.update_progress_style()

    def get_state(self) -> Dict[str, Any]:
        """获取组件状态"""
        return {
            'attribute': self.attribute_name,
            'value': self.current_value,
            'min': self.min_value,
            'max': self.max_value,
            'color': self.color,
            'display_name': self.display_name
        }

    def set_state(self, state: Dict[str, Any]):
        """设置组件状态"""
        if 'value' in state:
            self.set_value(state['value'])
        if 'min' in state and 'max' in state:
            self.set_range(state['min'], state['max'])
        if 'color' in state:
            self.set_color(state['color'])
        if 'display_name' in state:
            self.set_display_name(state['display_name'])
