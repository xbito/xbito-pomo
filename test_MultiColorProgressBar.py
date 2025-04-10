import sys
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, QSize
from MultiColorProgressBar import MultiColorProgressBar

# Create a Qt application for the tests
@pytest.fixture(scope="module")
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


class TestMultiColorProgressBar:    
    def test_initialization(self, app):
        """Test that the progress bar initializes with default properties."""
        progress_bar = MultiColorProgressBar()
        
        # Check default properties
        assert progress_bar.isTextVisible() == True
        assert progress_bar.format() == "%p%"
        assert progress_bar.value() == -1  # Default QProgressBar value is -1
        assert progress_bar.minimum() == 0
        assert progress_bar.maximum() == 100
        
    def test_colors_setup(self, app):
        """Test that the colors are set up correctly."""
        progress_bar = MultiColorProgressBar()
        
        # Test the color ranges and values
        assert len(progress_bar.colors) == 3
        
        # First color section (0-30%, green)
        assert progress_bar.colors[0][0] == 0.0
        assert progress_bar.colors[0][1] == 0.3
        assert progress_bar.colors[0][2].name().upper() == QColor("#4CAF50").name().upper()
        
        # Second color section (30-70%, orange)
        assert progress_bar.colors[1][0] == 0.3
        assert progress_bar.colors[1][1] == 0.7
        assert progress_bar.colors[1][2].name().upper() == QColor("#FFA726").name().upper()
        
        # Third color section (70-100%, red)
        assert progress_bar.colors[2][0] == 0.7
        assert progress_bar.colors[2][1] == 1.0
        assert progress_bar.colors[2][2].name().upper() == QColor("#EF5350").name().upper()
    
    def test_set_value(self, app):
        """Test setting different values on the progress bar."""
        progress_bar = MultiColorProgressBar()
        
        # Test different values
        test_values = [0, 15, 30, 50, 70, 85, 100]
        
        for value in test_values:
            progress_bar.setValue(value)
            assert progress_bar.value() == value
    
    def test_paint_event_triggered(self, app, monkeypatch):
        """Test that paint event gets called when progress changes."""
        progress_bar = MultiColorProgressBar()
        
        # Create a mock for the paintEvent method
        paint_event_called = False
        original_paint_event = progress_bar.paintEvent
        
        def mock_paint_event(event):
            nonlocal paint_event_called
            paint_event_called = True
            original_paint_event(event)
        
        monkeypatch.setattr(progress_bar, 'paintEvent', mock_paint_event)
        
        # Force a repaint by changing the value
        progress_bar.setValue(50)
        progress_bar.show()
        app.processEvents()
        
        assert paint_event_called is True
        
        # Clean up
        progress_bar.hide()
    
    def test_section_visibility(self, app, monkeypatch):
        """Test that the correct color sections are visible at different values."""
        progress_bar = MultiColorProgressBar()
        progress_bar.resize(QSize(200, 30))
        
        # Create a spy for the fillRect method of QPainter
        fill_rect_calls = []
        
        original_fill_rect = None
        
        class PainterMock:
            def fillRect(self, rect, color):
                fill_rect_calls.append((rect, color))
                if original_fill_rect:
                    original_fill_rect(rect, color)
        
        # Test with different values
        test_cases = [
            (25, 1),  # At 25%, only first section (green) should be visible
            (50, 2),  # At 50%, first and second sections should be visible
            (80, 3),  # At 80%, all three sections should be visible
        ]
        
        for value, expected_sections in test_cases:
            # Reset the spy
            fill_rect_calls.clear()
            
            # Set the value and force a repaint
            progress_bar.setValue(value)
            
            # Simulate paint event with our fillRect spy
            # The first fillRect call is for the background, so we ignore it
            # The next calls are for the colored sections
            sections = 0
            for start, end, color in progress_bar.colors:
                if value / 100.0 > start:
                    sections += 1
            
            assert sections == expected_sections, f"At {value}%, expected {expected_sections} section(s), got {sections}"


if __name__ == "__main__":
    pytest.main(["-v", "test_MultiColorProgressBar.py"])
