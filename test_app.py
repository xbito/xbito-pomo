import pytest
from PySide6.QtCore import Qt, QDate
from app import XbitoPomodoro


@pytest.fixture
def app(qtbot):
    """Create an instance of the XbitoPomodoro app"""
    phrase = "Stay focused and keep working!"
    pomodoro_app = XbitoPomodoro(qtbot, phrase)
    qtbot.addWidget(pomodoro_app)
    return pomodoro_app


def test_start_pause_button_initial_state(app):
    """Check the initial state of the start/pause button"""
    assert app.start_pause_button.text() == "Start"
    assert not app.is_timer_running


def test_start_button_starts_timer(app, qtbot):
    """Check if the start button starts the timer"""
    qtbot.mouseClick(app.start_pause_button, Qt.LeftButton)
    assert app.start_pause_button.text() == "Pause"
    assert app.is_timer_running


def test_pause_button_pauses_timer(app, qtbot):
    """Check if the pause button pauses the timer"""
    qtbot.mouseClick(app.start_pause_button, Qt.LeftButton)
    assert app.start_pause_button.text() == "Pause"
    assert app.is_timer_running

    # Pause the timer
    qtbot.mouseClick(app.start_pause_button, Qt.LeftButton)
    assert app.start_pause_button.text() == "Start"
    assert not app.is_timer_running


def test_timer_countdown(app, qtbot):
    """Check if the timer countdowns correctly"""
    # Start the timer
    qtbot.mouseClick(app.start_pause_button, Qt.LeftButton)
    assert app.is_timer_running

    # Wait for a few seconds to let the timer countdown
    qtbot.wait(2000)  # Wait for 2 seconds

    # Check if the remaining seconds have decreased
    assert app.remaining_seconds < app.initial_seconds

    # Pause the timer
    qtbot.mouseClick(app.start_pause_button, Qt.LeftButton)
    assert not app.is_timer_running

    # Store the remaining seconds
    remaining_seconds = app.remaining_seconds

    # Wait for a few seconds to ensure the timer is paused
    qtbot.wait(2000)

    # Check if the remaining seconds have not changed
    assert app.remaining_seconds == remaining_seconds


def test_date_month_year_day_label(app, qtbot):
    """Check if the date, month, year, and day labels are displayed correctly"""
    # Check if the date, month, year, and day labels are displayed
    current_date = QDate.currentDate()
    assert app.date_label.text() == current_date.toString("dd")
    assert app.month_label.text() == current_date.toString("MMM")
    assert app.year_label.text() == current_date.toString("yyyy")
    assert app.day_label.text() == current_date.toString("dddd")


def test_reverse_forward_buttons(app, qtbot):
    """Check if the reverse and forward buttons work correctly"""
    # Check if the reverse and forward buttons are enabled
    assert app.reverse_button.isEnabled()
    assert app.forward_button.isEnabled()
    # Click the forward button
    initial_seconds = app.remaining_seconds
    qtbot.mouseClick(app.forward_button, Qt.LeftButton)
    assert app.remaining_seconds > initial_seconds
    # Click the reverse button
    initial_seconds = app.remaining_seconds
    qtbot.mouseClick(app.reverse_button, Qt.LeftButton)
    assert app.remaining_seconds < initial_seconds
    # Click the fast forward button
    initial_seconds = app.remaining_seconds
    qtbot.mouseClick(app.fast_forward_button, Qt.LeftButton)
    assert app.remaining_seconds > initial_seconds
    # Click the fast reverse button
    initial_seconds = app.remaining_seconds
    qtbot.mouseClick(app.fast_reverse_button, Qt.LeftButton)
    assert app.remaining_seconds < initial_seconds
