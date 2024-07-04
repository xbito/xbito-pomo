from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor


class MultiColorProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = [
            (0.0, 0.3, QColor(0, 200, 0)),  # Less bright green: 0% to 30%
            (0.3, 0.7, QColor(200, 200, 0)),  # Less bright yellow: 30% to 70%
            (0.7, 1.0, QColor(200, 0, 0)),  # Less bright red: 70% to 100%
        ]

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        # Draw the background
        painter.fillRect(rect, self.palette().window())

        # Calculate the width of each section
        for start, end, color in self.colors:
            if self.value() / 100.0 <= start:
                break
            if self.value() / 100.0 < end:
                end = self.value() / 100.0

            section_rect = QRectF(
                rect.left() + rect.width() * start,
                rect.top(),
                rect.width() * (end - start),
                rect.height(),
            )

            painter.fillRect(section_rect, color)

        # Draw the border
        painter.setPen(self.palette().windowText().color())
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

        # Draw the text
        text = f"{self.value()}%"
        painter.setPen(self.palette().text().color())
        painter.drawText(rect, Qt.AlignCenter, text)

        painter.end()
