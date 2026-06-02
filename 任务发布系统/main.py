import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("任务随机发布器")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
