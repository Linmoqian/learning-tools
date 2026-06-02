from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem,
    QScrollArea, QWidget, QFrame, QCheckBox,
    QGroupBox, QRadioButton, QButtonGroup,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class FilterDialog(QDialog):
    filter_applied = Signal(dict)
    
    def __init__(self, db, all_tasks, current_filter=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.all_tasks = all_tasks
        self.current_filter = current_filter or {
            'tags': [],
            'mode': 'union',  # 'union' 或 'intersection'
            'repeat_types': [],
            'show_no_tags': False
        }
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("🔍 筛选条件")
        self.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(self)
        
        title = QLabel("筛选条件设置")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        layout.addWidget(title)
        
        tags_group = QGroupBox("🏷️ 标签筛选")
        tags_layout = QVBoxLayout(tags_group)
        
        mode_layout = QHBoxLayout()
        mode_label = QLabel("匹配模式：")
        mode_layout.addWidget(mode_label)
        
        self.union_radio = QRadioButton("并集（包含任一标签）")
        self.union_radio.setChecked(self.current_filter.get('mode', 'union') == 'union')
        self.intersection_radio = QRadioButton("交集（包含所有标签）")
        self.intersection_radio.setChecked(self.current_filter.get('mode', 'union') == 'intersection')
        
        mode_layout.addWidget(self.union_radio)
        mode_layout.addWidget(self.intersection_radio)
        mode_layout.addStretch()
        tags_layout.addLayout(mode_layout)
        
        self.tags_list = QListWidget()
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        
        all_tags = self.db.get_all_tags()
        for tag in all_tags:
            item = QListWidgetItem(f"#{tag}")
            item.setData(Qt.UserRole, tag)
            if tag in self.current_filter.get('tags', []):
                item.setSelected(True)
            self.tags_list.addItem(item)
        
        tags_layout.addWidget(self.tags_list)
        
        if not all_tags:
            empty_label = QLabel("（暂无标签）")
            empty_label.setStyleSheet("color: #999; padding: 20px;")
            tags_layout.addWidget(empty_label)
        
        tags_layout.addWidget(self.tags_list)
        layout.addWidget(tags_group)
        
        repeat_group = QGroupBox("🔄 任务类型")
        repeat_layout = QVBoxLayout(repeat_group)
        
        self.check_daily = QCheckBox("🔄 每日任务")
        self.check_weekly = QCheckBox("📅 每周任务")
        self.check_accumulation = QCheckBox("📚 复习任务")
        self.check_single = QCheckBox("📝 单次任务")
        
        repeat_types = self.current_filter.get('repeat_types', [])
        self.check_daily.setChecked('daily' in repeat_types or not repeat_types)
        self.check_weekly.setChecked('weekly' in repeat_types or not repeat_types)
        self.check_accumulation.setChecked('accumulation' in repeat_types or not repeat_types)
        self.check_single.setChecked('single' in repeat_types or not repeat_types)
        
        repeat_layout.addWidget(self.check_daily)
        repeat_layout.addWidget(self.check_weekly)
        repeat_layout.addWidget(self.check_accumulation)
        repeat_layout.addWidget(self.check_single)
        layout.addWidget(repeat_group)
        
        options_group = QGroupBox("其他选项")
        options_layout = QVBoxLayout(options_group)
        
        self.show_no_tags_check = QCheckBox("显示无标签任务")
        self.show_no_tags_check.setChecked(self.current_filter.get('show_no_tags', False))
        options_layout.addWidget(self.show_no_tags_check)
        layout.addWidget(options_group)
        
        layout.addStretch()
        
        button_box = QDialogButtonBox()
        confirm_btn = button_box.addButton("应用筛选", QDialogButtonBox.AcceptRole)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
            }
        """)
        cancel_btn = button_box.addButton("取消", QDialogButtonBox.RejectRole)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 20px;
                border-radius: 5px;
            }
        """)
        
        button_box.accepted.connect(self._apply_filter)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def _apply_filter(self):
        selected_tags = []
        for i in range(self.tags_list.count()):
            item = self.tags_list.item(i)
            if item.isSelected():
                selected_tags.append(item.data(Qt.UserRole))
        
        repeat_types = []
        if self.check_daily.isChecked():
            repeat_types.append('daily')
        if self.check_weekly.isChecked():
            repeat_types.append('weekly')
        if self.check_accumulation.isChecked():
            repeat_types.append('accumulation')
        if self.check_single.isChecked():
            repeat_types.append('single')
        
        mode = 'union' if self.union_radio.isChecked() else 'intersection'
        
        filter_result = {
            'tags': selected_tags,
            'mode': mode,
            'repeat_types': repeat_types,
            'show_no_tags': self.show_no_tags_check.isChecked()
        }
        
        self.filter_applied.emit(filter_result)
        self.accept()
    
    def get_filter(self):
        return self.current_filter


class TagFilterWidget(QFrame):
    filter_changed = Signal(dict)
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_filter = {
            'tags': [],
            'mode': 'union',
            'repeat_types': [],
            'show_no_tags': False
        }
        self._init_ui()
        self._refresh_tag_buttons()
    
    def _init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        
        top_row = QHBoxLayout()
        
        self.all_btn = QPushButton("全部")
        self.all_btn.setCheckable(True)
        self.all_btn.setChecked(True)
        self.all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #27AE60;
            }
        """)
        self.all_btn.clicked.connect(lambda: self._toggle_basic_filter("全部"))
        top_row.addWidget(self.all_btn)
        
        self.no_tags_btn = QPushButton("无标签")
        self.no_tags_btn.setCheckable(True)
        self.no_tags_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #34495e;
                border: 1px solid #ddd;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #E67E22;
                color: white;
                border-color: #D35400;
            }
        """)
        self.no_tags_btn.clicked.connect(lambda: self._toggle_basic_filter("无标签"))
        top_row.addWidget(self.no_tags_btn)
        
        top_row.addSpacing(20)
        
        self.mode_btn = QPushButton("并集")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setChecked(True)
        self.mode_btn.clicked.connect(self._toggle_mode)
        self.mode_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
            QPushButton:checked {
                background-color: #E74C3C;
            }
        """)
        top_row.addWidget(self.mode_btn)
        
        top_row.addStretch()
        
        add_tag_btn = QPushButton("➕ 添加标签")
        add_tag_btn.clicked.connect(self._add_new_tag)
        add_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
        """)
        top_row.addWidget(add_tag_btn)
        
        delete_tag_btn = QPushButton("🗑️ 删除标签")
        delete_tag_btn.clicked.connect(self._delete_selected_tag)
        delete_tag_btn.setStyleSheet("""
            QPushButton {
                background-color: #E74C3C;
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
        """)
        top_row.addWidget(delete_tag_btn)
        
        filter_btn = QPushButton("🔍 更多筛选")
        filter_btn.clicked.connect(self._open_filter_dialog)
        filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border-radius: 15px;
                padding: 5px 15px;
                font-size: 12px;
            }
        """)
        top_row.addWidget(filter_btn)
        
        main_layout.addLayout(top_row)
        
        self.tags_scroll = QScrollArea()
        self.tags_scroll.setWidgetResizable(True)
        self.tags_scroll.setMaximumHeight(60)
        self.tags_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tags_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.tags_container = QWidget()
        self.tags_layout = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 5, 0, 5)
        
        self.tags_scroll.setWidget(self.tags_container)
        main_layout.addWidget(self.tags_scroll)
    
    def _refresh_tag_buttons(self):
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        all_tags = self.db.get_all_tags()
        
        for tag in all_tags:
            tag_btn = QPushButton(f"#{tag}")
            tag_btn.setCheckable(True)
            if tag in self.current_filter.get('tags', []):
                tag_btn.setChecked(True)
            tag_btn.clicked.connect(lambda checked, t=tag: self._toggle_tag(t))
            tag_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    color: #34495e;
                    border: 1px solid #ddd;
                    border-radius: 15px;
                    padding: 5px 12px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #9B59B6;
                    color: white;
                    border-color: #8E44AD;
                }
            """)
            self.tags_layout.addWidget(tag_btn)
        
        self.tags_layout.addStretch()
    
    def _toggle_basic_filter(self, filter_type):
        if filter_type == "全部":
            self.no_tags_btn.setChecked(False)
            self.current_filter = {
                'tags': [],
                'mode': self.current_filter.get('mode', 'union'),
                'repeat_types': [],
                'show_no_tags': False
            }
        elif filter_type == "无标签":
            self.all_btn.setChecked(False)
            self.current_filter = {
                'tags': [],
                'mode': self.current_filter.get('mode', 'union'),
                'repeat_types': [],
                'show_no_tags': True
            }
        
        self._refresh_tag_buttons()
        self.filter_changed.emit(self.current_filter)
    
    def _toggle_mode(self):
        current_mode = self.current_filter.get('mode', 'union')
        new_mode = 'intersection' if current_mode == 'union' else 'union'
        self.current_filter['mode'] = new_mode
        
        if new_mode == 'union':
            self.mode_btn.setText("并集")
            self.mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border-radius: 15px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #E74C3C;
                }
            """)
        else:
            self.mode_btn.setText("交集")
            self.mode_btn.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border-radius: 15px;
                    padding: 5px 15px;
                    font-size: 12px;
                }
                QPushButton:checked {
                    background-color: #3498DB;
                }
            """)
        
        self.filter_changed.emit(self.current_filter)
    
    def _toggle_tag(self, tag):
        current_tags = self.current_filter.get('tags', [])
        
        if tag in current_tags:
            current_tags.remove(tag)
        else:
            current_tags.append(tag)
        
        self.all_btn.setChecked(False)
        self.no_tags_btn.setChecked(False)
        self.current_filter['tags'] = current_tags
        self.current_filter['show_no_tags'] = False
        
        self._refresh_tag_buttons()
        self.filter_changed.emit(self.current_filter)
    
    def _add_new_tag(self):
        from PySide6.QtWidgets import QInputDialog
        tag_name, ok = QInputDialog.getText(self, "添加标签", "请输入新标签名称：")
        if ok and tag_name.strip():
            tag_name = tag_name.strip()
            existing_tags = self.db.get_all_tags()
            if tag_name not in existing_tags:
                self.db.add_tag(tag_name)
            
            if tag_name not in self.current_filter.get('tags', []):
                self.current_filter.setdefault('tags', []).append(tag_name)
            
            self.all_btn.setChecked(False)
            self.no_tags_btn.setChecked(False)
            self.current_filter['show_no_tags'] = False
            
            self._refresh_tag_buttons()
            self.filter_changed.emit(self.current_filter)
    
    def _delete_selected_tag(self):
        if not self.current_filter.get('tags'):
            QMessageBox.information(self, "提示", "请先在下方标签中选择要删除的标签！")
            return
        
        from PySide6.QtWidgets import QInputDialog
        existing_tags = self.db.get_all_tags()
        if not existing_tags:
            QMessageBox.information(self, "提示", "没有可删除的标签！")
            return
        
        items = existing_tags
        current_tags_text = "\n".join([f"{i+1}. {tag}" for i, tag in enumerate(items)])
        
        selected, ok = QInputDialog.getItem(
            self, 
            "删除标签", 
            f"选择要删除的标签：\n{current_tags_text}",
            items,
            0,
            False
        )
        
        if ok and selected:
            self.db.delete_tag(selected)
            
            if selected in self.current_filter.get('tags', []):
                self.current_filter['tags'].remove(selected)
            
            self._refresh_tag_buttons()
            self.filter_changed.emit(self.current_filter)
    
    def _open_filter_dialog(self):
        from ..models.database import Database
        all_tasks = self.db.get_available_tasks_for_gacha()
        
        dialog = FilterDialog(self.db, all_tasks, self.current_filter, self)
        dialog.filter_applied.connect(self._on_filter_applied)
        dialog.exec()
    
    def _on_filter_applied(self, filter_dict):
        self.current_filter = filter_dict
        self.all_btn.setChecked(False)
        self.no_tags_btn.setChecked(False)
        
        if filter_dict['mode'] == 'union':
            self.mode_btn.setText("并集")
        else:
            self.mode_btn.setText("交集")
        
        self._refresh_tag_buttons()
        self.filter_changed.emit(filter_dict)
    
    def get_filter(self):
        return self.current_filter
    
    def reset_filter(self):
        self.all_btn.setChecked(True)
        self.no_tags_btn.setChecked(False)
        self.mode_btn.setChecked(True)
        self.mode_btn.setText("并集")
        self.current_filter = {
            'tags': [],
            'mode': 'union',
            'repeat_types': [],
            'show_no_tags': False
        }
        self._refresh_tag_buttons()
        self.filter_changed.emit(self.current_filter)
