import json
from typing import Dict, List, Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsLineItem,
    QMessageBox
)
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF, Signal
from PySide6.QtGui import (
    QFont, QColor, QPen, QBrush, QPainter,
    QLinearGradient, QPolygonF, QCursor
)

from ..models.database import Database
from ..services.task_service import TaskService


NODE_WIDTH = 160
NODE_HEIGHT = 64
NODE_RADIUS = 12
H_SPACING = 80
V_SPACING = 40


class GraphicsNodeItem(QGraphicsItem):
    def __init__(self, task_id: int, task_name: str, status: str,
                 waiting_for: str = "", parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self.task_name = task_name
        self.status = status
        self.waiting_for = waiting_for
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
        self.setAcceptHoverEvents(True)
        self._is_hovered = False
        self._is_connecting_source = False
        self.setZValue(1)
        self._db = None

        colors = {
            "completed": QColor(39, 174, 96),
            "unlocked": QColor(41, 128, 185),
            "locked": QColor(149, 165, 166),
            "skipped": QColor(230, 126, 34),
        }
        self._color = colors.get(status, QColor(149, 165, 166))

    def boundingRect(self):
        return QRectF(0, 0, NODE_WIDTH, NODE_HEIGHT).adjusted(-2, -2, 4, 4)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(0, 0, NODE_WIDTH, NODE_HEIGHT)

        shadow_offset = 3
        shadow_rect = rect.translated(0, shadow_offset)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
        painter.drawRoundedRect(shadow_rect, NODE_RADIUS, NODE_RADIUS)

        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        base_color = self._color
        gradient.setColorAt(0, base_color.lighter(120))
        gradient.setColorAt(1, base_color)
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(base_color.darker(130), 1.5))
        painter.drawRoundedRect(rect, NODE_RADIUS, NODE_RADIUS)

        if self._is_hovered:
            highlight = QColor(255, 255, 255, 30)
            painter.setBrush(QBrush(highlight))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, NODE_RADIUS, NODE_RADIUS)

        if self._is_connecting_source:
            painter.setPen(QPen(QColor(255, 193, 7), 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), NODE_RADIUS, NODE_RADIUS)

        text_rect = rect.adjusted(8, 4, -8, -4)
        font = QFont("Microsoft YaHei", 11, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        elided_text = painter.fontMetrics().elidedText(
            self.task_name, Qt.ElideRight, int(text_rect.width())
        )
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_text)

        if self.status == "locked" and self.waiting_for:
            sub_font = QFont("Microsoft YaHei", 8)
            painter.setFont(sub_font)
            painter.setPen(QColor(255, 255, 255, 180))
            sub_rect = text_rect.adjusted(0, 18, 0, 0)
            waiting_text = f"等待：{self.waiting_for}"
            elided_waiting = painter.fontMetrics().elidedText(
                waiting_text, Qt.ElideRight, int(sub_rect.width())
            )
            painter.drawText(sub_rect, Qt.AlignLeft | Qt.AlignVCenter, elided_waiting)
        elif self.status == "skipped":
            sub_font = QFont("Microsoft YaHei", 9)
            painter.setFont(sub_font)
            painter.setPen(QColor(255, 255, 255, 200))
            sub_rect = text_rect.adjusted(0, 18, 0, 0)
            painter.drawText(sub_rect, Qt.AlignLeft | Qt.AlignVCenter, "⏭️ 已跳过")

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            if hasattr(self, '_edges'):
                for edge in self._edges:
                    edge.adjust()
        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event):
        db = self._db or Database()
        task_dict = db.get_task(self.task_id)
        if task_dict:
            detail_parts = [
                f"📝 {task_dict['name']}",
                f"类型: {task_dict.get('task_type', 'normal')}",
                f"阻力: {task_dict.get('resistance', 'medium')} | 精力: {task_dict.get('energy_required', 'medium')}",
                f"优先级: {task_dict.get('priority', 5)}/10"
            ]
            prereq_ids = task_dict.get('prerequisite_ids', [])
            if isinstance(prereq_ids, str):
                try:
                    prereq_ids = json.loads(prereq_ids)
                except:
                    prereq_ids = []
            if prereq_ids:
                prereq_names = []
                for pid in prereq_ids:
                    prereq = db.get_task(pid)
                    if prereq:
                        prereq_names.append(prereq['name'])
                detail_parts.append(f"前置: {'、'.join(prereq_names)}")
            detail_parts.append(f"状态: {'已完成' if task_dict.get('completed') else '未完成'}")
            detail_parts.append(f"解锁: {'是' if task_dict.get('is_unlocked') else '否'}")

            QMessageBox.information(
                self.scene().views()[0] if self.scene().views() else None,
                f"任务详情 #{self.task_id}",
                "\n".join(detail_parts)
            )
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if scene:
                parent = scene.parent()
                if parent and hasattr(parent, '_handle_node_click'):
                    parent._handle_node_click(self)
        super().mousePressEvent(event)

    def _add_edge(self, edge):
        if not hasattr(self, '_edges'):
            self._edges = []
        self._edges.append(edge)

    def _remove_edge(self, edge):
        if hasattr(self, '_edges') and edge in self._edges:
            self._edges.remove(edge)

    def set_db(self, db):
        self._db = db


class EdgeItem(QGraphicsLineItem):
    def __init__(self, source_node: GraphicsNodeItem, target_node: GraphicsNodeItem):
        super().__init__()
        self.source = source_node
        self.target = target_node
        self._arrow_size = 8
        self.setZValue(0)
        self.setPen(QPen(QColor(189, 195, 199), 2, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin))
        self.setAcceptHoverEvents(True)
        self._is_hovered = False
        source_node._add_edge(self)
        target_node._add_edge(self)
        self.adjust()

    def adjust(self):
        if not self.source or not self.target:
            return
        source_center = self.source.pos() + QPointF(NODE_WIDTH / 2, NODE_HEIGHT / 2)
        target_center = self.target.pos() + QPointF(NODE_WIDTH / 2, NODE_HEIGHT / 2)
        line = QLineF(source_center, target_center)
        self.setLine(line)

    def paint(self, painter, option, widget=None):
        if not self.source or not self.target:
            return
        painter.setRenderHint(QPainter.Antialiasing)

        if self._is_hovered:
            painter.setPen(QPen(QColor(231, 76, 60), 3))
        else:
            painter.setPen(self.pen())
        painter.drawLine(self.line())

        arrow_p1 = self.line().p2() - QPointF(
            self._arrow_size * 1.2,
            -self._arrow_size * 0.6
        )
        arrow_p2 = self.line().p2() - QPointF(
            self._arrow_size * 1.2,
            self._arrow_size * 0.6
        )

        arrow = QPolygonF()
        arrow.append(self.line().p2())
        arrow.append(arrow_p1)
        arrow.append(arrow_p2)

        color = QColor(231, 76, 60) if self._is_hovered else QColor(189, 195, 199)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(arrow)

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            scene = self.scene()
            if scene:
                parent = scene.parent()
                if parent and hasattr(parent, '_handle_edge_right_click'):
                    parent._handle_edge_right_click(self, event)
                    return
        super().mousePressEvent(event)


class TempConnectLine(QGraphicsLineItem):
    def __init__(self, start_point: QPointF):
        super().__init__()
        self.setPen(QPen(QColor(255, 193, 7), 2, Qt.DashLine))
        self.setLine(QLineF(start_point, start_point))
        self.setZValue(10)

    def update_end(self, end_point: QPointF):
        start = self.line().p1()
        self.setLine(QLineF(start, end_point))


class DepGraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() > 0:
            self.scale(factor, factor)
        else:
            self.scale(1 / factor, 1 / factor)

    def mouseMoveEvent(self, event):
        scene = self.scene()
        if scene:
            parent = scene.parent()
            if parent and hasattr(parent, '_is_connecting') and parent._is_connecting:
                scene_pos = self.mapToScene(event.pos())
                parent._update_temp_line(scene_pos)
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if scene:
            parent = scene.parent()
            if parent and hasattr(parent, '_is_connecting') and parent._is_connecting:
                item = self.itemAt(event.pos())
                if not item:
                    parent._finish_connection(self.mapToScene(event.pos()), None)
                    return
        super().mouseReleaseEvent(event)


class DependencyGraphDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.task_service = TaskService(db)
        self._node_items: Dict[int, GraphicsNodeItem] = {}
        self._edge_items: List[EdgeItem] = []
        self._is_connecting = False
        self._connect_source: Optional[GraphicsNodeItem] = None
        self._temp_line: Optional[TempConnectLine] = None
        self._init_ui()
        self._build_graph()

    def _init_ui(self):
        self.setWindowTitle("🔗 任务依赖关系图")
        self.resize(900, 680)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        header_layout = QHBoxLayout()
        title = QLabel("🔗 任务依赖关系图")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        legend = QLabel(
            "🟢 已完成 &nbsp;&nbsp;"
            "🔵 已解锁 &nbsp;&nbsp;"
            "⭕ 锁定中 &nbsp;&nbsp;"
            "🟠 已跳过"
        )
        legend.setStyleSheet("font-size: 12px; color: #7f8c8d;")
        header_layout.addWidget(legend)
        main_layout.addLayout(header_layout)

        info = QLabel(
            "💡 双击节点查看详情 · "
            "箭头方向 A→B 表示 B 依赖 A · "
            "右键连线删除依赖"
        )
        info.setStyleSheet("font-size: 11px; color: #95a5a6;")
        main_layout.addWidget(info)

        self.scene = QGraphicsScene(self)
        self.view = DepGraphView(self.scene, self)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.setStyleSheet("""
            QGraphicsView {
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                background-color: white;
            }
        """)
        main_layout.addWidget(self.view)

        tool_layout = QHBoxLayout()

        self.connect_btn = QPushButton("✏️ 添加依赖")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #E67E22;
                color: white;
            }
            QPushButton:hover {
                background-color: #D35400;
            }
            QPushButton:checked {
                background-color: #D35400;
                border: 2px solid #F39C12;
            }
        """)
        self.connect_btn.setCheckable(True)
        self.connect_btn.toggled.connect(self._toggle_connect_mode)
        tool_layout.addWidget(self.connect_btn)

        mode_hint = QLabel("")
        mode_hint.setStyleSheet("font-size: 12px; color: #E67E22; font-weight: bold;")
        self._mode_hint = mode_hint
        tool_layout.addWidget(mode_hint)

        tool_layout.addStretch()

        reset_btn = QPushButton("🔄 自动排列")
        reset_btn.clicked.connect(self._auto_layout)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        tool_layout.addWidget(reset_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95A5A6;
                color: white;
            }
            QPushButton:hover {
                background-color: #7F8C8D;
            }
        """)
        tool_layout.addWidget(close_btn)

        main_layout.addLayout(tool_layout)

    def _toggle_connect_mode(self, checked):
        self._is_connecting = checked
        if checked:
            self._mode_hint.setText("点击一个任务作为前置条件（源），再点击另一个任务作为后续任务（目标）")
            self.view.setDragMode(QGraphicsView.NoDrag)
            self.setCursor(QCursor(Qt.CrossCursor))
        else:
            self._mode_hint.setText("")
            self.view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.setCursor(QCursor(Qt.ArrowCursor))
            self._clear_connection_state()

    def _clear_connection_state(self):
        if self._connect_source:
            self._connect_source._is_connecting_source = False
            self._connect_source.update()
            self._connect_source = None
        if self._temp_line and self._temp_line.scene():
            self.scene.removeItem(self._temp_line)
            self._temp_line = None

    def _handle_node_click(self, node: GraphicsNodeItem):
        if not self._is_connecting:
            return

        if not self._connect_source:
            self._connect_source = node
            node._is_connecting_source = True
            node.update()
            center = node.pos() + QPointF(NODE_WIDTH / 2, NODE_HEIGHT / 2)
            self._temp_line = TempConnectLine(center)
            self.scene.addItem(self._temp_line)
            self._mode_hint.setText(
                f"已选源任务：{node.task_name}，请点击目标任务"
            )
            return

        source_id = self._connect_source.task_id
        source_name = self._connect_source.task_name
        dest_id = node.task_id
        dest_name = node.task_name

        self._clear_connection_state()

        if source_id == dest_id:
            QMessageBox.information(self, "提示", "不能将任务设为依赖自身")
            self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")
            return

        task_dict = self.db.get_task(dest_id)
        if not task_dict:
            self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")
            return

        try:
            current_prereq_raw = task_dict.get('prerequisite_ids', '[]')
            current_prereq_ids = json.loads(current_prereq_raw) if current_prereq_raw else []
        except (json.JSONDecodeError, TypeError):
            current_prereq_ids = []

        if source_id in current_prereq_ids:
            QMessageBox.information(self, "提示",
                f"依赖关系已存在：\n{source_name} → {dest_name}")
            self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")
            return

        proposed_ids = current_prereq_ids + [source_id]

        if self.task_service.detect_cycle(dest_id, proposed_ids):
            QMessageBox.warning(self, "循环依赖",
                f"❌ 检测到循环依赖！\n"
                f"设置「{dest_name}」依赖「{source_name}」"
                f"将产生循环。")
            self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")
            return

        prereq_dict = self.db.get_task(source_id)
        if prereq_dict and not prereq_dict.get('completed'):
            is_unlocked = False
        else:
            other_prereq_all_done = all(
                (self.db.get_task(pid) or {}).get('completed', False)
                for pid in proposed_ids if pid != source_id
            )
            is_unlocked = other_prereq_all_done and (prereq_dict and prereq_dict.get('completed'))

        self.db.update_task(
            dest_id,
            prerequisite_ids=proposed_ids,
            is_unlocked=is_unlocked or False
        )

        QMessageBox.information(self, "依赖已添加",
            f"✅ 已添加依赖：\n"
            f"「{dest_name}」现在依赖「{source_name}」")
        self._build_graph()
        self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")

    def _update_temp_line(self, scene_pos: QPointF):
        if self._temp_line:
            self._temp_line.update_end(scene_pos)

    def _finish_connection(self, scene_pos: QPointF, item_at_pos):
        if not item_at_pos and self._connect_source:
            self._clear_connection_state()
            self._mode_hint.setText("点击一个任务作为前置条件，再点击另一个任务作为后续任务")

    def _handle_edge_right_click(self, edge: EdgeItem, event):
        source_name = edge.source.task_name
        target_name = edge.target.task_name

        reply = QMessageBox.question(
            self, "删除依赖关系",
            f"确定要删除这条依赖吗？\n\n"
            f"「{target_name}」将不再依赖「{source_name}」\n\n"
            f"如果被依赖任务未完成，目标任务将被锁定。",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            target_id = edge.target.task_id
            source_id = edge.source.task_id

            task_dict = self.db.get_task(target_id)
            if task_dict:
                try:
                    prereq_raw = task_dict.get('prerequisite_ids', '[]')
                    prereq_ids = json.loads(prereq_raw) if prereq_raw else []
                except (json.JSONDecodeError, TypeError):
                    prereq_ids = []

                if source_id in prereq_ids:
                    prereq_ids.remove(source_id)

                    if not prereq_ids:
                        is_unlocked = True
                    else:
                        is_unlocked = all(
                            (self.db.get_task(pid) or {}).get('completed', False)
                            for pid in prereq_ids
                        )

                    self.db.update_task(
                        target_id,
                        prerequisite_ids=prereq_ids,
                        is_unlocked=is_unlocked
                    )

                    QMessageBox.information(self, "依赖已删除",
                        f"✅ 已删除依赖关系\n"
                        f"「{target_name}」不再依赖「{source_name}」")
                    self._build_graph()

    def _build_graph(self):
        self.scene.clear()
        self._node_items.clear()
        self._edge_items.clear()

        tasks = self.db.get_all_tasks_with_prerequisites()

        if not tasks:
            text = self.scene.addText("暂无任务数据", QFont("Microsoft YaHei", 14))
            text.setDefaultTextColor(QColor(189, 195, 199))
            text.setPos(300, 200)
            return

        for t in tasks:
            task_id = t['id']
            task_name = t['name']
            completed = t.get('completed', False)
            is_unlocked = t.get('is_unlocked', False)
            prereq_ids = t.get('prerequisite_ids', [])

            if completed:
                status = "completed"
            elif is_unlocked:
                status = "unlocked"
            else:
                status = "locked"

            waiting_names = []
            if status == "locked" and prereq_ids:
                for pid in prereq_ids:
                    prereq = self.db.get_task(pid)
                    if prereq and not prereq.get('completed'):
                        waiting_names.append(prereq['name'])
            waiting_for = "、".join(waiting_names[:2])
            if len(waiting_names) > 2:
                waiting_for += "..."

            node = GraphicsNodeItem(task_id, task_name, status, waiting_for)
            node.set_db(self.db)
            self.scene.addItem(node)
            self._node_items[task_id] = node

        for t in tasks:
            task_id = t['id']
            prereq_ids = t.get('prerequisite_ids', [])
            target_node = self._node_items.get(task_id)
            if not target_node:
                continue
            for pid in prereq_ids:
                source_node = self._node_items.get(pid)
                if source_node:
                    edge = EdgeItem(source_node, target_node)
                    self.scene.addItem(edge)
                    self._edge_items.append(edge)

        self._auto_layout()

    def _auto_layout(self):
        tasks = self.db.get_all_tasks_with_prerequisites()
        if not tasks:
            return

        layers = self._compute_layers(tasks)

        current_y = 40
        for layer_idx, layer in enumerate(layers):
            count = len(layer)
            total_width = count * NODE_WIDTH + (count - 1) * H_SPACING
            start_x = max(40, (self.view.width() - total_width) / 2)

            for i, task_id in enumerate(layer):
                node = self._node_items.get(task_id)
                if node:
                    node.setPos(QPointF(start_x + i * (NODE_WIDTH + H_SPACING), current_y))

            current_y += NODE_HEIGHT + V_SPACING

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))

    def _compute_layers(self, tasks: List[Dict]) -> List[List[int]]:
        task_map = {t['id']: t for t in tasks}
        in_degree = {}
        for t in tasks:
            in_degree[t['id']] = len(t.get('prerequisite_ids', []))

        layers = []
        remaining = set(t['id'] for t in tasks)

        while remaining:
            current_layer = [tid for tid in remaining if in_degree.get(tid, 0) == 0]
            if not current_layer:
                current_layer = list(remaining)
            layers.append(current_layer)
            for tid in current_layer:
                remaining.discard(tid)
                for other_id in list(remaining):
                    other_task = task_map.get(other_id, {})
                    prereqs = other_task.get('prerequisite_ids', [])
                    if tid in prereqs:
                        in_degree[other_id] = max(0, in_degree.get(other_id, 0) - 1)

        return layers