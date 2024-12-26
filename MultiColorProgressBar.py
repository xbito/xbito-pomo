from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QProgressBar
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor


class MultiColorProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = [
            (0.0, 0.3, QColor("#4CAF50")),  # Muted green for morning
            (0.3, 0.7, QColor("#FFA726")),  # Muted orange for mid-day
            (0.7, 1.0, QColor("#EF5350")),  # Muted red for evening
        ]
        self.setTextVisible(True)
        self.setFormat("%p%")
        self.setStyleSheet("QProgressBar { color: white; }")

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
