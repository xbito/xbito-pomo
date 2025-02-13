from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt

class TreeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = 1
        self.load_tree_images()

    def load_tree_images(self):
        """Load tree stage images from assets folder"""
        self.tree_images = {}
        for i in range(1, 5):  # Stages 1-4
            image_path = f"assets/tree_stage{i}.png"
            self.tree_images[i] = QPixmap(image_path)

    def set_stage(self, stage):
        """Set the tree growth stage (1-4)"""
        print(f"Stage before: {self.stage}")
        self.stage = min(max(stage, 1), 4)  # Clamp between 1 and 4
        self.update()
        print(f"Stage after: {self.stage}")

    def paintEvent(self, event):
        if self.stage in self.tree_images:
            painter = QPainter(self)
            pixmap = self.tree_images[self.stage]
            
            # Define scaling factors for each stage
            scale_factors = {
                1: 0.8,  # 20% smaller
                2: 0.8,  # 20% smaller
                3: 1.2,  # 20% bigger
                4: 1.28  # 28% bigger
            }
            
            # Get base size that would fit the widget while maintaining aspect ratio
            base_scaled_pixmap = pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Apply the stage-specific scaling
            scale_factor = scale_factors[self.stage]
            final_width = int(base_scaled_pixmap.width() * scale_factor)
            final_height = int(base_scaled_pixmap.height() * scale_factor)
            
            # Scale with the stage-specific factor
            final_scaled_pixmap = pixmap.scaled(
                final_width,
                final_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Center the image in the widget
            x = (self.width() - final_scaled_pixmap.width()) // 2
            y = (self.height() - final_scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, final_scaled_pixmap)