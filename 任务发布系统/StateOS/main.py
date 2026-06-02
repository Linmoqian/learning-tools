#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StateOS - 个人状态管理系统
主程序入口 - 修复版
"""

import sys
import os
import traceback
from pathlib import Path

# 添加详细日志
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("StateOS 启动")
print("=" * 60)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from core.database import DatabaseManager
from core.state_engine import StateEngine
from ui.main_window import MainWindow
from ui.morning_assessment import MorningAssessmentDialog
from config.config_manager import get_config_manager


class StateOSApp:
    """主应用程序类 - 修复版"""

    def __init__(self):
        print("[主程序] 初始化开始...")

        try:
            self.app = QApplication(sys.argv)
            self.setup_application()
            print("[主程序] Qt应用初始化完成")

            # 初始化配置管理器
            print("[主程序] 初始化配置管理器...")
            self.config_manager = get_config_manager()
            print("[主程序] 配置管理器完成")

            # 初始化数据库管理器
            print("[主程序] 初始化数据库管理器...")
            self.db_manager = DatabaseManager()
            print("[主程序] 数据库管理器完成")

            # 初始化状态引擎
            print("[主程序] 初始化状态引擎...")
            self.state_engine = StateEngine(self.db_manager)
            print("[主程序] 状态引擎完成")

            # 检查是否需要晨间评估
            print("[主程序] 检查晨间评估...")
            if self.should_show_morning_assessment():
                print("[主程序] 需要显示晨间评估")
                self.show_morning_assessment()
            else:
                print("[主程序] 不需要晨间评估，显示主窗口")
                self.show_main_window()

        except Exception as e:
            print(f"[主程序] 初始化失败: {e}")
            traceback.print_exc()
            sys.exit(1)

    def setup_application(self):
        """应用程序设置"""
        self.app.setApplicationName("StateOS")
        self.app.setOrganizationName("PersonalSystems")

        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.app.setFont(font)

    def should_show_morning_assessment(self):
        """检查是否需要显示晨间评估"""
        try:
            today = self.db_manager.get_today_date()
            print(f"[主程序] 检查今天: {today}")
            has_checkin = self.db_manager.has_daily_checkin(today)
            print(f"[主程序] 是否有记录: {has_checkin}")
            return not has_checkin
        except Exception as e:
            print(f"[主程序] 检查晨间评估时出错: {e}")
            return True

    def show_morning_assessment(self):
        """显示晨间评估对话框"""
        print("[主程序] 显示晨间评估对话框")
        try:
            self.assessment_dialog = MorningAssessmentDialog(self.db_manager)
            self.assessment_dialog.assessment_completed.connect(self.on_assessment_completed)
            self.assessment_dialog.exec()
        except Exception as e:
            print(f"[主程序] 显示晨间评估时出错: {e}")
            # 出错时直接显示主窗口
            self.show_main_window()

    def on_assessment_completed(self, initial_state):
        """晨间评估完成回调"""
        print(f"[主程序] 晨间评估完成，初始状态: {initial_state}")
        try:
            self.state_engine.set_current_state(initial_state)
            self.show_main_window()
        except Exception as e:
            print(f"[主程序] 设置初始状态时出错: {e}")
            self.show_main_window()

    def show_main_window(self):
        """显示主窗口"""
        print("[主程序] 显示主窗口")
        try:
            self.main_window = MainWindow(self.db_manager, self.state_engine)
            self.main_window.show()
            print("[主程序] 主窗口显示完成")

            # 设置退出时保存状态
            self.app.aboutToQuit.connect(self.on_application_quit)

        except Exception as e:
            print(f"[主程序] 显示主窗口时出错: {e}")
            traceback.print_exc()
            sys.exit(1)

    def on_application_quit(self):
        """应用程序退出处理"""
        print("[主程序] 应用程序退出中...")
        try:
            self.state_engine.save_current_state()
            self.db_manager.close()
            print("[主程序] 状态保存完成")
        except Exception as e:
            print(f"[主程序] 退出时保存状态失败: {e}")

    def run(self):
        """运行应用程序"""
        print("[主程序] 进入主事件循环")
        try:
            return self.app.exec()
        except Exception as e:
            print(f"[主程序] 主循环异常: {e}")
            traceback.print_exc()
            return 1


def main():
    """主函数 - 修复版"""
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print(f"脚本路径: {__file__}")

    try:
        app = StateOSApp()
        exit_code = app.run()
        print(f"\n[主程序] 退出代码: {exit_code}")
        return exit_code
    except Exception as e:
        print(f"[主程序] 应用程序启动失败: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())