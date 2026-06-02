"""
战术指令按钮组件
自定义战术指令按钮
"""

from PyQt6.QtWidgets import QPushButton, QLabel, QVBoxLayout, QWidget, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QPalette, QColor, QPainter, QPen, QBrush, QIcon
import math


class TacticalButton(QPushButton):
    """战术指令按钮组件"""

    activated = pyqtSignal(str)  # 按钮激活信号，传递指令名称

    def __init__(self, command_name: str, display_name: str,
                 description: str, color: str = "#3498db",
                 icon: str = "", parent=None):
        super().__init__(parent)
        self.command_name = command_name
        self.display_name = display_name
        self.description = description
        self.base_color = color
        self.icon_text = icon
        self.is_active = False
        self.cooldown = 0  # 冷却时间（秒）
        self.cooldown_remaining = 0
        self.cooldown_timer = None

        self.setup_ui()
        self.setup_effects()

    def setup_ui(self):
        """设置UI"""
        # 设置按钮文本
        self.setText(f"{self.icon_text} {self.display_name}")

        # 设置字体
        font = QFont("Microsoft YaHei", 11, QFont.Weight.Bold)
        self.setFont(font)

        # 设置样式
        self.update_button_style()

        # 设置固定高度
        self.setMinimumHeight(60)

        # 设置工具提示
        self.setToolTip(f"{self.description}\n\n指令: {self.command_name}")

        # 连接点击信号
        self.clicked.connect(self.on_clicked)

    def setup_effects(self):
        """设置特效"""
        # 创建冷却定时器
        self.cooldown_timer = QTimer(self)
        self.cooldown_timer.timeout.connect(self.update_cooldown)

    def update_button_style(self):
        """更新按钮样式"""
        if self.is_active:
            # 激活状态 - 更亮的颜色
            active_color = self.lighten_color(self.base_color, 30)
            style = f"""
                QPushButton {{
                    background-color: {active_color};
                    color: white;
                    border: 2px solid {self.darken_color(self.base_color, 20)};
                    border-radius: 8px;
                    padding: 10px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(self.base_color, 40)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(self.base_color, 10)};
                }}
                QPushButton:disabled {{
                    background-color: #95a5a6;
                    color: #bdc3c7;
                }}
            """
        else:
            # 正常状态
            style = f"""
                QPushButton {{
                    background-color: {self.base_color};
                    color: white;
                    border: 2px solid {self.darken_color(self.base_color, 20)};
                    border-radius: 8px;
                    padding: 10px;
                    text-align: center;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(self.base_color, 20)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(self.base_color, 10)};
                }}
                QPushButton:disabled {{
                    background-color: #95a5a6;
                    color: #bdc3c7;
                }}
            """

        self.setStyleSheet(style)

    def on_clicked(self):
        """按钮点击处理"""
        if self.cooldown_remaining > 0:
            # 冷却中，不执行
            self.show_cooldown_tooltip()
            return

        # 激活按钮
        self.activate()

        # 发出激活信号
        self.activated.emit(self.command_name)

    def activate(self):
        """激活按钮"""
        self.is_active = True
        self.update_button_style()

        # 3秒后恢复
        QTimer.singleShot(3000, self.deactivate)

    def deactivate(self):
        """取消激活按钮"""
        self.is_active = False
        self.update_button_style()

    def set_cooldown(self, seconds: int):
        """设置冷却时间"""
        self.cooldown = max(0, seconds)
        self.cooldown_remaining = self.cooldown

        if self.cooldown > 0:
            self.setEnabled(False)
            self.cooldown_timer.start(1000)  # 每秒更新一次
        else:
            self.setEnabled(True)

    def update_cooldown(self):
        """更新冷却时间"""
        if self.cooldown_remaining > 0:
            self.cooldown_remaining -= 1

            # 更新按钮文本显示剩余时间
            if self.cooldown_remaining > 0:
                self.setText(f"{self.icon_text} {self.display_name} ({self.cooldown_remaining}s)")
            else:
                self.setText(f"{self.icon_text} {self.display_name}")
                self.setEnabled(True)
                self.cooldown_timer.stop()
        else:
            self.cooldown_timer.stop()

    def show_cooldown_tooltip(self):
        """显示冷却时间工具提示"""
        # 在按钮位置显示临时提示
        tooltip_text = f"冷却中... 剩余 {self.cooldown_remaining} 秒"

        # 使用自定义工具提示
        tooltip_pos = self.mapToGlobal(QPoint(0, self.height()))
        QToolTip.showText(tooltip_pos, tooltip_text, self, self.rect(), 2000)

    def lighten_color(self, color_hex: str, amount: int) -> str:
        """变亮颜色"""
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)

        r = min(255, r + amount)
        g = min(255, g + amount)
        b = min(255, b + amount)

        return f"#{r:02x}{g:02x}{b:02x}"

    def darken_color(self, color_hex: str, amount: int) -> str:
        """变暗颜色"""
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)

        r = max(0, r - amount)
        g = max(0, g - amount)
        b = max(0, b - amount)

        return f"#{r:02x}{g:02x}{b:02x}"

    def set_color(self, color: str):
        """设置按钮颜色"""
        self.base_color = color
        self.update_button_style()

    def set_description(self, description: str):
        """设置描述"""
        self.description = description
        self.setToolTip(f"{self.description}\n\n指令: {self.command_name}")

    def set_icon(self, icon_text: str):
        """设置图标文本"""
        self.icon_text = icon_text
        if self.cooldown_remaining > 0:
            self.setText(f"{icon_text} {self.display_name} ({self.cooldown_remaining}s)")
        else:
            self.setText(f"{icon_text} {self.display_name}")

    def get_info(self) -> dict:
        """获取按钮信息"""
        return {
            'command_name': self.command_name,
            'display_name': self.display_name,
            'description': self.description,
            'color': self.base_color,
            'icon': self.icon_text,
            'cooldown': self.cooldown,
            'cooldown_remaining': self.cooldown_remaining,
            'is_active': self.is_active
        }

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        # 如果正在冷却，绘制冷却覆盖层
        if self.cooldown_remaining > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 半透明黑色覆盖层
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(self.rect(), 8, 8)

            # 绘制进度圆弧（冷却进度）
            if self.cooldown > 0:
                progress = 1.0 - (self.cooldown_remaining / self.cooldown)
                start_angle = 90 * 16  # 12点钟方向开始
                span_angle = -progress * 360 * 16  # 顺时针

                # 设置圆弧颜色
                painter.setPen(QPen(QColor(255, 255, 255, 200), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)

                # 计算圆弧区域（稍微内缩）
                margin = 10
                arc_rect = self.rect().adjusted(margin, margin, -margin, -margin)
                painter.drawArc(arc_rect, start_angle, span_angle)

                # 绘制冷却时间文本
                painter.setPen(QPen(Qt.GlobalColor.white))
                painter.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                                 f"{self.cooldown_remaining}s")
