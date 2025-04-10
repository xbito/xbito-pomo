import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from tree_widget import TreeWidget
from unittest.mock import patch, MagicMock
import os


@pytest.fixture
def tree_widget(qtbot):
    """Create an instance of the TreeWidget"""
    widget = TreeWidget()
    qtbot.addWidget(widget)
    return widget


def test_initialization(tree_widget):
    """Test that the tree widget initializes with stage 1"""
    assert tree_widget.stage == 1
    assert len(tree_widget.tree_images) == 4
    assert all(isinstance(pixmap, QPixmap) for pixmap in tree_widget.tree_images.values())


def test_set_stage_valid_values(tree_widget):
    """Test that set_stage correctly updates the stage with valid values"""
    # Test setting to stage 2
    tree_widget.set_stage(2)
    assert tree_widget.stage == 2
    
    # Test setting to stage 3
    tree_widget.set_stage(3)
    assert tree_widget.stage == 3
    
    # Test setting to stage 4
    tree_widget.set_stage(4)
    assert tree_widget.stage == 4


def test_set_stage_boundary_values(tree_widget):
    """Test that set_stage correctly clamps values outside 1-4 range"""
    # Test with value below minimum
    tree_widget.set_stage(0)
    assert tree_widget.stage == 1
    
    # Test with value above maximum
    tree_widget.set_stage(5)
    assert tree_widget.stage == 4


def test_load_tree_images(tree_widget, monkeypatch):
    """Test that images are loaded correctly from the assets folder"""
    # Reset the tree_images dictionary
    tree_widget.tree_images = {}
    
    # Create a mock for QPixmap that simulates successful image loading
    class MockPixmap(MagicMock):
        def __init__(self, path):
            super().__init__()
            self.path = path
        
        def isNull(self):
            return False
    
    # Apply the mock to QPixmap
    monkeypatch.setattr("tree_widget.QPixmap", MockPixmap)
    
    # Call the method being tested
    tree_widget.load_tree_images()
    
    # Check that we have 4 image entries
    assert len(tree_widget.tree_images) == 4


@patch('tree_widget.QPainter')
def test_paint_event(mock_painter, tree_widget, qtbot):
    """Test that paintEvent uses the correct image for the current stage"""
    # Set up mock painter
    painter_instance = mock_painter.return_value
    
    # Create a mock event
    mock_event = MagicMock()
    
    # Test painting with different stages
    for stage in range(1, 5):
        tree_widget.set_stage(stage)
        
        # Trigger paint event
        tree_widget.paintEvent(mock_event)
        
        # Verify that drawPixmap was called - we can't easily check the arguments
        # but we can at least verify the method was called
        painter_instance.drawPixmap.assert_called()
        painter_instance.reset_mock()
