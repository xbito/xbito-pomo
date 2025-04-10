import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMenuBar
import platform
import sys
from unittest.mock import patch, MagicMock
from app import XbitoPomodoro
from menu import AppMenu


@pytest.fixture
def app_with_menu(qtbot):
    """Create an instance of the XbitoPomodoro app with menu"""
    phrase = "Stay focused and keep working!"
    pomodoro_app = XbitoPomodoro(qtbot, phrase)
    qtbot.addWidget(pomodoro_app)
    
    # Save references to menu bar and its components to prevent garbage collection
    pomodoro_app._menu_bar = pomodoro_app.menuBar()
    pomodoro_app._menus = []
    pomodoro_app._menu_actions = {}  # Store all menu actions
    
    # Get all menu actions and store references
    for i in range(len(pomodoro_app._menu_bar.actions())):
        action = pomodoro_app._menu_bar.actions()[i]
        menu = action.menu()
        if menu:
            pomodoro_app._menus.append(menu)
            # Store all actions for each menu
            menu_actions = []
            for j in range(len(menu.actions())):
                menu_action = menu.actions()[j]
                menu_actions.append(menu_action)
            pomodoro_app._menu_actions[menu.title()] = menu_actions
    
    # Process must be called to ensure Qt processes all pending events
    qtbot.wait(100)
    
    return pomodoro_app


def test_menu_creation(app_with_menu):
    """Test if the menu is created with all expected items"""
    menu_bar = app_with_menu._menu_bar  # Use stored reference
    assert menu_bar is not None
    assert len(app_with_menu._menus) > 0
    
    # Get menu items from stored references
    menu_items = [action.text() for action in app_with_menu._menu_actions["Menu"]]
    assert menu_items, "Menu actions should not be empty"
    
    # Check standard menu items
    assert "About" in menu_items
    assert "Settings" in menu_items
    assert "Report" in menu_items
    assert "Send to Back" in menu_items
    
    # Check platform-specific menu items
    if platform.system() == "Windows":
        assert "Launch at Startup" in menu_items
    else:
        assert "Launch at Startup" not in menu_items


def test_about_dialog(app_with_menu, qtbot, monkeypatch):
    """Test if the About dialog appears when clicked"""
    # Mock the show_dialog method
    mock_show_dialog = MagicMock()
    monkeypatch.setattr(app_with_menu, "show_dialog", mock_show_dialog)
    
    # Get About action from stored references
    about_action = None
    for action in app_with_menu._menu_actions["Menu"]:
        if action.text() == "About":
            about_action = action
            break
    
    assert about_action is not None
    
    # Trigger the action
    about_action.trigger()
    
    # Check if show_dialog was called with the right parameters
    mock_show_dialog.assert_called_once()
    args = mock_show_dialog.call_args[0]
    assert args[0] == "About"
    assert "Xbito - Pomodoro Timer" in args[1]
    assert "Version" in args[1]


def test_settings_dialog(app_with_menu, qtbot, monkeypatch):
    """Test if the Settings dialog appears when clicked"""
    # Create a mock for QDialog.exec
    original_exec = QDialog.exec
    mock_exec = MagicMock(return_value=1)  # Return value doesn't matter for this test
    
    # Apply the monkeypatch
    monkeypatch.setattr(QDialog, "exec", mock_exec)
    
    # Get Settings action from stored references
    settings_action = None
    for action in app_with_menu._menu_actions["Menu"]:
        if action.text() == "Settings":
            settings_action = action
            break
    
    assert settings_action is not None
    
    # Trigger the action
    settings_action.trigger()
    
    # Check if dialog exec was called
    assert mock_exec.called
    
    # Restore original exec
    monkeypatch.setattr(QDialog, "exec", original_exec)


def test_report_dialog(app_with_menu, qtbot, monkeypatch):
    """Test if the Report dialog appears when clicked"""
    # Create a mock for QDialog.exec
    original_exec = QDialog.exec
    mock_exec = MagicMock(return_value=1)  # Return value doesn't matter for this test
    
    # Apply the monkeypatch
    monkeypatch.setattr(QDialog, "exec", mock_exec)
    
    # Get Report action from stored references
    report_action = None
    for action in app_with_menu._menu_actions["Menu"]:
        if action.text() == "Report":
            report_action = action
            break
    
    assert report_action is not None
    
    # Trigger the action
    report_action.trigger()
    
    # Check if dialog exec was called
    assert mock_exec.called
    
    # Restore original exec
    monkeypatch.setattr(QDialog, "exec", original_exec)


def test_send_to_back(app_with_menu, qtbot, monkeypatch):
    """Test if the Send to Back action works"""
    # Mock the send_to_back method
    mock_send_to_back = MagicMock()
    monkeypatch.setattr(app_with_menu, "send_to_back", mock_send_to_back)
    
    # Get Send to Back action from stored references
    send_to_back_action = None
    for action in app_with_menu._menu_actions["Menu"]:
        if action.text() == "Send to Back":
            send_to_back_action = action
            break
    
    assert send_to_back_action is not None
    
    # Trigger the action
    send_to_back_action.trigger()
    
    # Check if send_to_back was called
    mock_send_to_back.assert_called_once()


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
def test_is_startup_enabled(app_with_menu, monkeypatch):
    """Test is_startup_enabled function on Windows"""
    # Skip this test if not on Windows
    if platform.system() != "Windows":
        return
        
    # Create scenarios to test
    scenarios = [
        # Scenario 1: Registry entry exists
        {
            'mock_openkey': MagicMock(return_value="key"),
            'mock_queryvalueex': MagicMock(return_value=("path", 1)),
            'expected_result': True,
            'mock_queryvalueex_side_effect': None
        },
        # Scenario 2: Registry entry doesn't exist
        {
            'mock_openkey': MagicMock(return_value="key"),
            'mock_queryvalueex': MagicMock(),
            'expected_result': False,
            'mock_queryvalueex_side_effect': FileNotFoundError()
        },
        # Scenario 3: Error opening registry
        {
            'mock_openkey': MagicMock(side_effect=Exception("Registry error")),
            'mock_queryvalueex': MagicMock(),
            'expected_result': False,
            'mock_queryvalueex_side_effect': None
        }
    ]
    
    # Run tests for each scenario
    for scenario in scenarios:
        mock_openkey = scenario['mock_openkey']
        mock_queryvalueex = scenario['mock_queryvalueex']
        if scenario['mock_queryvalueex_side_effect']:
            mock_queryvalueex.side_effect = scenario['mock_queryvalueex_side_effect']
            
        mock_closekey = MagicMock()
        
        # Apply the monkeypatch
        import winreg
        monkeypatch.setattr(winreg, "OpenKey", mock_openkey)
        monkeypatch.setattr(winreg, "QueryValueEx", mock_queryvalueex)
        monkeypatch.setattr(winreg, "CloseKey", mock_closekey)
        
        # Test is_startup_enabled
        result = app_with_menu.menu.is_startup_enabled()
        assert result == scenario['expected_result']
