import sys
from math import sin, cos, radians
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath
from PySide6.QtCore import Qt


def draw_leaf(painter, x, y, size=15, angle=0):
    painter.save()
    painter.translate(x, y)
    painter.rotate(angle)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(QColor("#228B22")))

    # A simple "two-lobed" curved leaf
    leaf_path = QPainterPath()
    leaf_path.moveTo(0, 0)
    leaf_path.cubicTo(
        -size * 0.5,
        -size * 0.8,  # control point 1
        size * 0.5,
        -size * 0.8,  # control point 2
        size,
        0,  # end point
    )
    leaf_path.cubicTo(
        size * 0.5,
        size * 0.8,  # control point 3
        -size * 0.5,
        size * 0.8,  # control point 4
        0,
        0,  # back to start
    )

    painter.drawPath(leaf_path)
    painter.restore()


class TreeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = 1

        # We'll define data in a dictionary for each stage:
        #  "trunk_height": how tall the trunk is
        #  "trunk_width": thickness of the trunk line
        #  "leaf_size": general size of leaves
        #  "branches": list of (distance_from_trunk_top, angle_degrees, length, leaf_angle)
        #     angle_degrees is measured from the horizontal axis, 0 pointing right,
        #     90 up, 180 left, 270 down, etc.
        #     We pick angles around 135..180 for left, 0..45 for right, so the tree is balanced.
        self.stages_data = {
            1: {"trunk_height": 40, "trunk_width": 4, "leaf_size": 14, "branches": []},
            2: {
                "trunk_height": 60,
                "trunk_width": 5,
                "leaf_size": 16,
                "branches": [
                    # left branch ~145°, right branch ~35°
                    (15, 145, 20, 145),
                    (15, 35, 20, 35),
                ],
            },
            3: {
                "trunk_height": 80,
                "trunk_width": 6,
                "leaf_size": 18,
                "branches": [
                    (10, 115, 25, 115),  # top left angled upwards
                    (10, 65, 25, 65),  # top right angled upwards
                    (30, 135, 20, 135),  # lower left
                    (30, 45, 20, 45),  # lower right
                ],
            },
            4: {
                "trunk_height": 100,
                "trunk_width": 7,
                "leaf_size": 20,
                "branches": [
                    (10, 120, 30, 120),  # top left
                    (10, 60, 30, 60),  # top right
                    (25, 135, 30, 135),  # mid left
                    (25, 45, 30, 45),  # mid right
                    (45, 150, 20, 150),  # lower left
                    (45, 30, 20, 30),  # lower right
                ],
            },
            5: {
                "trunk_height": 120,
                "trunk_width": 8,
                "leaf_size": 22,
                "branches": [
                    (5, 110, 35, 110),  # top left angled more upward
                    (5, 70, 35, 70),  # top right angled more upward
                    (25, 130, 30, 130),  # mid left
                    (25, 50, 30, 50),  # mid right
                    (45, 140, 20, 140),  # lower left
                    (45, 40, 20, 40),  # lower right
                ],
            },
        }

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Grab data for current stage
        data = self.stages_data.get(self.stage, self.stages_data[1])
        trunk_height = data["trunk_height"]
        trunk_width = data["trunk_width"]
        leaf_size = data["leaf_size"]
        branches = data["branches"]

        trunk_color = QColor("#8B4513")  # brown
        w = self.width()
        h = self.height()

        # We'll position the trunk in the bottom center
        center_x = w // 2
        bottom_y = h - 20
        top_y = bottom_y - trunk_height

        # Draw trunk
        trunk_pen = QPen(
            trunk_color, trunk_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin
        )
        painter.setPen(trunk_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(center_x, bottom_y, center_x, top_y)

        # A leaf at the trunk's top
        draw_leaf(painter, center_x, top_y - leaf_size * 0.5, leaf_size, 0)

        # Draw branches
        for info in branches:
            offset_y, angle_deg, length, leaf_angle = info
            branch_start_y = top_y + offset_y
            branch_start_x = center_x

            # Convert angle to radians
            theta = radians(angle_deg)
            branch_end_x = branch_start_x + length * cos(theta)
            branch_end_y = branch_start_y + length * sin(theta)

            # Draw the branch
            painter.drawLine(branch_start_x, branch_start_y, branch_end_x, branch_end_y)

            # Draw a leaf at the branch end
            draw_leaf(painter, branch_end_x, branch_end_y, leaf_size, leaf_angle)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tree Growth Stages")

        self.tree_widget = TreeWidget()

        # Buttons to move through stages
        btn_layout = QHBoxLayout()
        for i in range(1, 6):
            btn = QPushButton(f"Stage {i}")
            btn.clicked.connect(lambda checked, s=i: self.set_stage(s))
            btn_layout.addWidget(btn)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tree_widget)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def set_stage(self, stage_number):
        self.tree_widget.stage = stage_number
        self.tree_widget.update()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(500, 500)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
