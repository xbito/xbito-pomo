import os
import sys
import logging
import platform
import ctypes

if platform.system() == "Windows":
    import win32api
    import win32con
    import win32gui

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QDialog,
    QSpinBox,
)
from PySide6.QtCore import QTimer, Qt, QDate

from datetime import datetime, time, timedelta

from MultiColorProgressBar import MultiColorProgressBar
from db import (
    init_db,
    insert_pomodoro_session,
    update_pomodoro_session,
    fetch_focus_summary,
    get_setting,
    save_setting,
    delete_setting,
)
from motivation import get_motivational_phrase
from yoga import get_desk_yoga_stretch

from sound import play_celebratory_melody, play_rest_end_melody, play_bell_sound
from menu import AppMenu


class XbitoPomodoro(QMainWindow):
    def __init__(self, app, phrase):
        self.debug_mode = (
            "TERM_PROGRAM" in os.environ.keys()
            and os.environ["TERM_PROGRAM"] == "vscode"
        )
        # Initialize the database with unified init_db function
        init_db()
        self.phrase = phrase
        self.app = app
        self.start_time = None  # To store the session start time
        # Check if running in a debug session
        if self.debug_mode:
            logging.debug("Running in debug mode.")
            self.initial_seconds = 15  # 15 seconds for debug mode
            self.rest_seconds = 10  # 10 seconds for Rest timer in debug mode
            self.long_rest_seconds = 20  # 20 seconds for Long Rest timer in debug mode
            self.update_motivational_phrase_seconds = 30  # 30 seconds for debug mode
            self.session_alert_miliseconds = 10 * 1000  # 10 seconds for debug mode
        else:
            self.initial_seconds = 1800  # 30 minutes
            self.rest_seconds = 300  # 5 minutes for Rest timer
            self.long_rest_seconds = 900  # 15 minutes for Long Rest timer
            self.update_motivational_phrase_seconds = 21600  # 6 hours
            self.session_alert_miliseconds = 10 * 60 * 1000  # 10 minutes
        self.sessions_before_long_rest = 2  # Number of sessions before a long rest
        # Settings need to be loaded before we compute remaining_seconds
        self.load_settings()
        self.completed_sessions = 0  # Track the number of completed sessions
        self.remaining_seconds = self.initial_seconds
        self.is_timer_running = False  # Track timer state
        self.session_alert_triggered = False  # Track if the alert has been triggered
        super().__init__()
        self.setup_window()
        # Create a central widget and layout
        centralWidget = QWidget()
        self.layout = QVBoxLayout(centralWidget)
        self.setup_date_day_label()
        self.setup_progress_bar()
        self.update_progress_bar()
        self.setCentralWidget(centralWidget)
        self.setup_timer()
        self.setup_timer_type_label()
        self.setup_controls_layout()
        self.setup_start_pause_button()
        self.setup_emoticon_buttons()
        self.setup_motivational_phrase()
        self.setup_focus_summary()
        self.menu = AppMenu(self)  # Initialize the AppMenu
        self.apply_dark_theme()
        self.adjustSize()
        self.setup_session_alert_timer()  # Add this line to initialize the session alert timer

    def load_settings(self):
        """
        Loads settings from the database.
        """
        self.initial_seconds = get_setting("focus_duration", self.initial_seconds)
        self.rest_seconds = get_setting("short_break_duration", self.rest_seconds)
        self.long_rest_seconds = get_setting(
            "long_break_duration", self.long_rest_seconds
        )
        self.sessions_before_long_rest = get_setting(
            "sessions_before_long_break", self.sessions_before_long_rest
        )

    def save_settings(self):
        """
        Saves the settings from the dialog and updates the application state.
        """
        multiplier = 1 if self.debug_mode else 60

        new_initial_seconds = self.focus_spinbox.value() * multiplier
        new_rest_seconds = self.short_break_spinbox.value() * multiplier
        new_long_rest_seconds = self.long_break_spinbox.value() * multiplier
        new_sessions_before_long_rest = self.sessions_spinbox.value()

        # Save settings only if they differ from the default values
        if new_initial_seconds != self.initial_seconds:
            save_setting("focus_duration", new_initial_seconds)
        else:
            delete_setting("focus_duration")

        if new_rest_seconds != self.rest_seconds:
            save_setting("short_break_duration", new_rest_seconds)
        else:
            delete_setting("short_break_duration")

        if new_long_rest_seconds != self.long_rest_seconds:
            save_setting("long_break_duration", new_long_rest_seconds)
        else:
            delete_setting("long_break_duration")

        if new_sessions_before_long_rest != self.sessions_before_long_rest:
            save_setting("sessions_before_long_break", new_sessions_before_long_rest)
        else:
            delete_setting("sessions_before_long_break")

        # Update the application state
        self.initial_seconds = new_initial_seconds
        self.rest_seconds = new_rest_seconds
        self.long_rest_seconds = new_long_rest_seconds
        self.sessions_before_long_rest = new_sessions_before_long_rest

        # Update the remaining seconds if the timer is not running
        if not self.is_timer_running:
            if self.timer_type == "Focus":
                self.remaining_seconds = self.initial_seconds
            elif self.timer_type == "Rest":
                self.remaining_seconds = self.rest_seconds
            self.update_countdown_display()

        # Close the settings dialog
        self.sender().parent().accept()

    def send_to_back(self):
        """
        Sends the application window to the back of the screen.
        """
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
        QTimer.singleShot(15000, self.bring_to_front_delayed)

    def bring_to_front_delayed(self):
        """
        Brings the application window to the front after a short delay.
        """
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.show()

    def setup_timer_type_label(self):
        """
        Sets up the timer type label in the UI.

        This method creates a QLabel widget to display the current timer type in the UI.
        It sets the initial timer type to "Focus" and applies the necessary styling and alignment.
        The QLabel widget is then added to the layout.

        """
        self.timer_type = "Focus"  # Attribute to track the current timer type
        self.timer_type_label = QLabel(
            self.timer_type
        )  # Display the timer type in the UI
        self.timer_type_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.timer_type_label.setAlignment(
            Qt.AlignCenter
        )  # Center-align the timer type label

        self.layout.addWidget(self.timer_type_label)

    def setup_timer(self):
        """
        Sets up the timer for updating the progress bar and countdown.

        This method creates two QTimer objects: `update_timer` and `timer`.
        The `update_timer` is used to update the progress bar every minute,
        while the `timer` is used to automatically update the countdown.
        """
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress_bar)
        self.update_timer.start(60000)  # Update every minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_update_countdown)

    def setup_start_pause_button(self):
        """
        Set up the start/pause button and reset button.

        This method creates the start/pause button and reset button, sets their styles,
        and connects them to their respective functions.
        """
        self.start_pause_button = QPushButton("Start")
        self.start_pause_button.setStyleSheet("font-size: 18px; padding: 5px;")
        self.start_pause_button.clicked.connect(self.toggle_timer)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("font-size: 18px; padding: 5px;")
        self.reset_button.clicked.connect(self.click_reset_timer)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_pause_button, 1)
        button_layout.addWidget(self.reset_button, 1)

        self.layout.addLayout(button_layout)

    def setup_controls_layout(self):
        """
        Set up the controls layout for the application.

        This method creates control buttons for adjusting the timer, adds a countdown label,
        and adds all the controls to the main layout.
        """
        self.controls_layout = QHBoxLayout()
        # Create control buttons
        self.reverse_button = QPushButton("-")
        self.fast_reverse_button = QPushButton("--")
        self.forward_button = QPushButton("+")
        self.fast_forward_button = QPushButton("++")

        self.reverse_button.clicked.connect(lambda: self.manually_adjust_timer(-1))
        self.fast_reverse_button.clicked.connect(lambda: self.manually_adjust_timer(-5))
        self.forward_button.clicked.connect(lambda: self.manually_adjust_timer(1))
        self.fast_forward_button.clicked.connect(lambda: self.manually_adjust_timer(5))

        # Add buttons to the controls layout
        self.controls_layout.addWidget(self.fast_reverse_button)
        self.controls_layout.addWidget(self.reverse_button)

        minutes, seconds = divmod(self.remaining_seconds, 60)
        self.countdown_label = QLabel(f"{minutes:02d}:{seconds:02d}")
        self.countdown_label.setStyleSheet("font-size: 24px;")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        # Add the countdown label to the controls layout
        self.controls_layout.addWidget(self.countdown_label)
        self.controls_layout.addWidget(self.forward_button)
        self.controls_layout.addWidget(self.fast_forward_button)
        # Add the controls layout to the main layout
        self.layout.addLayout(self.controls_layout)

    def setup_emoticon_buttons(self):
        """
        Set up the emoticon buttons in the user interface.
        Connect the buttons to the corresponding feedback recording functions.
        Enable/disable the buttons based on the application's state.
        Add tooltips to the buttons.
        """
        self.happy_button = QPushButton("👍")
        self.yoga_button = QPushButton("🧘")
        self.sad_button = QPushButton("👎")
        self.happy_button.clicked.connect(lambda: self.record_feedback("happy"))
        self.yoga_button.clicked.connect(self.show_yoga_stretch)
        self.sad_button.clicked.connect(lambda: self.record_feedback("sad"))
        # Add emoticon buttons to the layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.happy_button)
        self.button_layout.addWidget(self.yoga_button)
        self.button_layout.addWidget(self.sad_button)
        self.layout.addLayout(self.button_layout)
        self.happy_button.setEnabled(False)
        self.yoga_button.setEnabled(False)
        self.sad_button.setEnabled(False)
        # Add tooltips to the emoticon buttons
        self.happy_button.setToolTip("Happy/Positive")
        self.yoga_button.setToolTip("Yoga Stretch")
        self.sad_button.setToolTip("Sad/Negative")

    def show_yoga_stretch(self):
        """
        Displays a yoga stretch in a dialog box.
        """
        yoga_stretch = get_desk_yoga_stretch()
        self.show_dialog("Desk Yoga Stretch", yoga_stretch)

    def setup_window(self):
        """
        Set up the window properties and position.

        This method sets the window title, width, height, position, and flags.
        """
        self.setWindowTitle("Xbito - Pomodoro Timer")
        # Set the window to a fixed width of 380 pixels
        self.setMinimumWidth(380)
        self.setGeometry(100, 100, 380, 115)
        self.setMaximumWidth(380)
        # Positioning the window near the top right of the screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        x = screen_geometry.width() * 0.9 - self.width()  # 10% from the right edge
        y = screen_geometry.height() * 0.1  # 10% from the top
        self.move(int(x), int(y))
        # Set the window to always stay on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def setup_motivational_phrase(self):
        """
        Display motivational Phrase in the screen, allowing for multi-line if it exceeds the width.
        When the phrase is too long, it will wrap to the next line.

        Add a timer to update the motivational phrase every 6 hours.
        """
        self.motivational_phrase_label = QLabel(self.phrase)
        self.motivational_phrase_label.setWordWrap(True)  # Enable word wrapping
        self.motivational_phrase_label.setAlignment(Qt.AlignCenter)
        self.motivational_phrase_label.setStyleSheet(
            "font-size: 15px; font-weight: bold;"
        )
        self.layout.insertWidget(0, self.motivational_phrase_label)
        self.update_motivational_phrase_timer = QTimer(self)
        self.update_motivational_phrase_timer.timeout.connect(
            self.update_motivational_phrase
        )
        self.update_motivational_phrase_timer.start(
            self.update_motivational_phrase_seconds * 1000
        )  # Update every 6 hours

    def update_motivational_phrase(self):
        """
        Update the motivational phrase displayed in the UI.

        This method fetches a new motivational phrase and updates the label in the UI.
        """
        self.phrase = get_motivational_phrase()
        self.motivational_phrase_label.setText(self.phrase)

    def setup_date_day_label(self):
        """
        Initializes the date and day labels.

        This method gets the current date and formats it into separate labels for the day, date, month, and year.
        It also sets the styles and alignments for each label, and adds them to the main layout of the dialog.
        """
        # Get the current date
        current_date = QDate.currentDate()

        # Format the date
        date_text = current_date.toString("dd")
        month_text = current_date.toString("MMM")
        year_text = current_date.toString("yyyy")
        day_text = current_date.toString("dddd")

        # Create labels
        self.date_label = QLabel(date_text)
        self.month_label = QLabel(month_text)
        self.year_label = QLabel(year_text)
        self.day_label = QLabel(day_text)

        # Set styles
        self.date_label.setStyleSheet(
            "color: white; font-size: 50px; font-weight: bold;"
        )
        self.month_label.setStyleSheet(
            "color: white; font-size: 18px; font-weight: bold;"
        )
        self.year_label.setStyleSheet("color: white; font-size: 18px;")
        self.day_label.setStyleSheet("color: white; font-size: 18px;")

        # Align text
        self.date_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.month_label.setAlignment(Qt.AlignLeft)
        self.year_label.setAlignment(Qt.AlignLeft)
        self.day_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Create date layout
        date_layout = QVBoxLayout()
        date_layout.addWidget(self.month_label)
        date_layout.addWidget(self.year_label)
        date_layout.setSpacing(2)  # Reduce space between month and year

        # Create main layout for date and day
        date_day_layout = QHBoxLayout()
        date_day_layout.setSpacing(1)
        date_day_layout.addWidget(self.date_label)
        date_day_layout.addLayout(date_layout)
        date_day_layout.addWidget(self.day_label)

        # Add the date and day layout to the main layout of the dialog
        self.layout.addLayout(date_day_layout)

    def setup_progress_bar(self):
        self.progress_bar = MultiColorProgressBar(self)
        self.layout.addWidget(self.progress_bar)

    def toggle_timer(self):
        """
        Toggles the timer on or off.

        If the timer is not running, it starts the timer and sets the start time.
        If the timer is running, it stops the timer and enables the happy and sad buttons.
        If the timer is paused, it resumes the timer and disables the happy and sad buttons.

        Returns:
            None
        """
        if self.is_timer_running:
            # The button is currently the Pause button
            self.click_pause_timer()
        else:
            # The button is currently the Start button
            self.click_start_timer()

    def click_start_timer(self):
        """
        Starts the timer based on the current timer type.

        This method sets the start time of the session, starts the timer, and updates the UI to reflect the timer's state.
        It also disables the happy, yoga, and sad buttons to prevent user input during the session.
        """
        if not self.is_timer_running:
            # Only set the start time if the timer is not already running
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.timer.start(1000)  # Update every second
        self.is_timer_running = True
        self.start_pause_button.setText("Pause")
        self.happy_button.setEnabled(False)
        self.yoga_button.setEnabled(False)
        self.sad_button.setEnabled(False)
        # If timer type label is "Next: Rest", change it to "Rest" when starting the timer
        if (
            self.timer_type_label.text() == "Next: Rest"
            or self.timer_type_label.text() == "Next: Long Rest"
        ):
            self.timer_type_label.setText("Rest")
            self.timer_type = "Rest"
        elif self.timer_type_label.text() == "Next: Focus":
            self.timer_type_label.setText("Focus")
            self.timer_type = "Focus"
        # If after changing the timer_type it is Focus then record the start time
        if self.timer_type == "Focus":
            insert_pomodoro_session(self.start_time, None, "pending")
        self.reset_session_alert_timer()  # Reset the session alert timer when a session starts
        self.session_alert_triggered = False  # Reset the session alert triggered flag

    def click_pause_timer(self):
        """
        Pauses the timer.

        This method:
        - Stops the timer
        - Sets the timer running flag to False
        - Changes the start/pause button text to "Start"
        - Enables the happy, yoga, and sad buttons

        This allows the user to pause their current session and provide feedback if needed.
        """
        self.timer.stop()
        self.is_timer_running = False
        self.start_pause_button.setText("Start")
        self.happy_button.setEnabled(True)
        self.yoga_button.setEnabled(True)
        self.sad_button.setEnabled(True)
        self.reset_session_alert_timer()  # Reset the session alert timer when a pause happens
        self.session_alert_triggered = False  # Reset the session alert triggered flag

    def click_reset_timer(self, from_feedback=False):
        """
        Resets the timer to its initial state.

        This method stops the timer, resets the remaining seconds to the initial duration,
        updates the countdown label and button text, disables the happy and sad buttons,
        and sets the timer running flag to False.
        """
        self.timer.stop()
        # If the label is "Next: Rest" set the remaining seconds to the Rest timer duration
        # If the label is "Next: Focus" set the remaining seconds to the Focus timer duration
        if self.timer_type_label.text() == "Next: Rest":
            self.remaining_seconds = self.rest_seconds
        elif self.timer_type_label.text() == "Next: Long Rest":
            self.remaining_seconds = self.long_rest_seconds
        elif self.timer_type_label.text() == "Next: Focus":
            self.remaining_seconds = self.initial_seconds
        else:
            # Reset happened somewhere else, not at the end of a session, so reset to the Focus timer duration
            self.remaining_seconds = self.initial_seconds
        self.update_countdown_display()
        self.start_pause_button.setText("Start")
        self.is_timer_running = False
        self.happy_button.setEnabled(False)
        self.yoga_button.setEnabled(False)
        self.sad_button.setEnabled(False)
        if not from_feedback:
            # On Reset always set the timer type to Focus, but if coming from Feedback let the natural flow go on.
            self.timer_type = "Focus"
            self.timer_type_label.setText("Focus")
        self.reset_session_alert_timer()  # Reset the session alert timer when a reset happens
        self.session_alert_triggered = False  # Reset the session alert triggered flag

    def auto_stop_timer(self):
        """
        A session has completed.
        - changes the start/pause button text to "Start",
        - enables the feedback buttons
        - attempts to play a melody. If an error occurs while playing the melody, logs the error.
        """
        self.timer.stop()
        self.start_pause_button.setText("Start")
        self.is_timer_running = False
        # Play the corresponding melody
        logging.debug(f"Playing melody: {self.timer_type}")
        if self.timer_type == "Focus":
            # Record the session as completed
            update_pomodoro_session(
                self.start_time,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pending",
            )
            try:
                play_celebratory_melody()
            except Exception as e:
                logging.error(f"Error playing melody: {e}")
            self.happy_button.setEnabled(True)
            self.yoga_button.setEnabled(True)
            self.sad_button.setEnabled(True)
            self.completed_sessions += 1
            if self.completed_sessions % self.sessions_before_long_rest == 0:
                self.timer_type_label.setText("Next: Long Rest")
                self.remaining_seconds = self.long_rest_seconds
            else:
                self.timer_type_label.setText("Next: Rest")
                self.remaining_seconds = self.rest_seconds
        elif self.timer_type == "Rest":
            try:
                play_rest_end_melody()
            except Exception as e:
                logging.error(f"Error playing melody: {e}")
            self.timer_type_label.setText("Next: Focus")
            self.remaining_seconds = self.initial_seconds
        # Convert self.remaining_seconds to minutes and seconds for the countdown label
        self.update_countdown_display()
        self.reset_session_alert_timer()  # Reset the session alert timer when a session finishes normally
        self.session_alert_triggered = False  # Reset the session alert triggered flag

    def auto_update_countdown(self):
        """
        Automatically updates the countdown timer and handles actions when the timer reaches zero.

        Decreases the remaining seconds by 1 and updates the countdown label with the new time.
        If the remaining seconds reach zero:
        - stops the timer
        """
        self.remaining_seconds -= 1
        self.update_countdown_display()
        if self.remaining_seconds <= 0:
            self.auto_stop_timer()

    def manually_adjust_timer(self, minutes_change):
        """
        Adjusts the timer by the specified number of minutes.

        Args:
            minutes_change (int): The number of minutes to adjust the timer by.

        """
        # Convert minutes to seconds
        seconds_change = minutes_change * 60
        new_remaining_seconds = self.remaining_seconds + seconds_change

        # Ensure the timer is within the 1 to 120 minutes range
        if new_remaining_seconds < 60:
            self.remaining_seconds = 60  # Minimum of 1 minute
        elif new_remaining_seconds > 7200:
            self.remaining_seconds = 7200  # Maximum of 120 minutes
        else:
            self.remaining_seconds = new_remaining_seconds

        self.update_countdown_display()

    def update_countdown_display(self):
        """
        Updates the countdown display with the remaining time in minutes and seconds.
        """
        minutes, seconds = divmod(self.remaining_seconds, 60)
        self.countdown_label.setText(f"{minutes:02d}:{seconds:02d}")

    def record_feedback(self, feeling):
        """
        Records the feedback for a completed pomodoro session.

        Args:
            feeling (str): The feeling associated with the completed session.

        """
        if self.start_time:
            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            update_pomodoro_session(self.start_time, end_time, feeling)
            self.start_time = None  # Reset start time after recording feedback
            self.click_reset_timer(from_feedback=True)

    def update_progress_bar(self):
        """
        Updates the progress bar based on the current time.

        The progress bar represents the progress of the day, from 5 AM to 11 PM.
        If the current time is before 5 AM, the progress is 0.
        If the current time is after 11 PM, the progress is 100.
        Otherwise, the progress is calculated based on the current time compared to the start and end time of the day.
        """
        current_time = datetime.now()
        start_time = datetime.combine(
            current_time.date(), time(5, 0)
        )  # Day starts at 5 AM
        end_time = datetime.combine(
            current_time.date(), time(23, 0)
        )  # Day ends at 11 PM
        total_day_seconds = (end_time - start_time).total_seconds()
        current_seconds = (current_time - start_time).total_seconds()
        if current_time < start_time:
            progress = 0
        elif current_time > end_time:
            progress = 100
        else:
            progress = (current_seconds / total_day_seconds) * 100
        self.progress_bar.setValue(int(progress))

    def apply_dark_theme(self):
        # Set the dark theme for the window
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #333333;
                color: #ffffff;
            }
            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: 1px solid #777777;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #aaaaaa;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                background-color: #2B2B2B;
                border: none;
                border-radius: 2px;
                text-align: center;
                margin-top: 8px;
                margin-bottom: 8px;
                height: 4px;
                max-height: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
            QDialog {
                background-color: #333333;
                color: #ffffff;
            }

            QLabel {
                color: #ffffff;
            }

            QLabel#about_title {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 10px;
            }

            QLabel#about_text {
                margin-bottom: 20px;
            }

            QLabel#about_link {
                color: #22aa22;
                text-decoration: none;
            }

            QLabel#about_link:hover {
                text-decoration: underline;
            }
        """
        )

    def show_dialog(self, title, text, show_snooze=False):
        """
        Displays a dialog with the specified title and text.

        Args:
            title (str): The title of the dialog.
            text (str): The text content of the dialog.
            show_snooze (bool): Whether to show the snooze button.

        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()

        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)

        if show_snooze:
            button_layout = QHBoxLayout()
            snooze_button = QPushButton("Snooze")
            ok_button = QPushButton("OK")

            snooze_duration_spinbox = QSpinBox()
            snooze_duration_spinbox.setRange(
                1, 60
            )  # Allow snooze duration from 1 to 60 minutes
            snooze_duration_spinbox.setValue(
                10
            )  # Default snooze duration is 10 minutes
            button_layout.addWidget(snooze_duration_spinbox)

            snooze_button.clicked.connect(
                lambda: self.handle_snooze(dialog, snooze_duration_spinbox.value())
            )
            ok_button.clicked.connect(dialog.accept)

            button_layout.addWidget(snooze_button)
            button_layout.addWidget(ok_button)
            layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec()

    def handle_snooze(self, dialog, snooze_duration=None):
        """
        Handles the snooze action by resetting the session alert timer based on the specified snooze duration.
        """
        self.reset_session_alert_timer(snooze_duration)
        dialog.accept()

    def closeEvent(self, event):
        logging.debug("Application close event triggered. Resetting timer.")
        if platform.system() == "Windows":
            # Unregister power notifications
            if hasattr(self, "power_notify"):
                win32gui.UnregisterPowerSettingNotification(self.power_notify)
        self.click_reset_timer()
        event.accept()  # Ensures the window closes smoothly

    def setup_focus_summary(self):
        """
        Sets up the focus summary label in the UI.
        """
        self.focus_summary_label = QLabel()
        self.focus_summary_label.setWordWrap(True)
        self.focus_summary_label.setAlignment(Qt.AlignCenter)
        self.focus_summary_label.setStyleSheet("font-size: 12px;")
        self.layout.addWidget(self.focus_summary_label)

        # Update focus summary initially and set up a timer to update it periodically
        self.update_focus_summary()
        self.focus_summary_timer = QTimer(self)
        self.focus_summary_timer.timeout.connect(self.update_focus_summary)
        self.focus_summary_timer.start(300000)  # Update every 5 minutes

    def update_focus_summary(self):
        """
        Updates the focus summary label with the latest data.
        """
        summary = fetch_focus_summary()
        summary_text = (
            f"Focus Time (avg/day last week): {summary['week_avg']:.1f} min\n"
            f"Yesterday: {summary['yesterday']:.1f} min | Today: {summary['today']:.1f} min"
        )
        self.focus_summary_label.setText(summary_text)

    def setup_session_alert_timer(self, snooze_duration=None):
        """
        Sets up a timer to alert the user if a session has not started within the specified snooze duration.
        """
        if snooze_duration is None:
            snooze_duration_milliseconds = self.session_alert_miliseconds
        else:
            snooze_duration_milliseconds = snooze_duration * 60 * 1000
        print("Starting the session alert timer at", datetime.now())
        print(
            "Should alert at",
            datetime.now() + timedelta(milliseconds=snooze_duration_milliseconds),
        )
        self.session_alert_timer = QTimer(self)
        self.session_alert_timer.timeout.connect(self.trigger_session_alert)
        self.session_alert_timer.start(snooze_duration_milliseconds)

    def reset_session_alert_timer(self, snooze_duration=None):
        """
        Resets the session alert timer.
        """
        if snooze_duration is None:
            snooze_duration_milliseconds = self.session_alert_miliseconds
        else:
            snooze_duration_milliseconds = snooze_duration * 60 * 1000
        print("Reset the session alert timer at", datetime.now())
        print(
            "Should alert at",
            datetime.now() + timedelta(milliseconds=snooze_duration_milliseconds),
        )
        self.session_alert_timer.start(snooze_duration_milliseconds)
        self.session_alert_triggered = False  # Reset the session alert triggered flag

    def trigger_session_alert(self):
        """
        Triggers an alert if no session has started within the specified snooze duration.
        """
        if not self.is_timer_running and not self.session_alert_triggered:
            play_bell_sound()
            self.session_alert_triggered = True  # Ensure the alert happens only once
            self.show_dialog(
                "Alert",
                "You haven't started a session. Did you forget?",
                show_snooze=True,
            )

    def nativeEvent(self, eventType, message):
        """Handle native Windows events including power notifications"""
        if platform.system() == "Windows":
            msg = ctypes.wintypes.MSG.from_address(int(message))
            if msg.message == win32con.WM_POWERBROADCAST:
                if msg.wParam == win32con.PBT_APMRESUMEAUTOMATIC:
                    self.handle_resume_from_suspend()
        return False, 0

    def handle_resume_from_suspend(self):
        """Handle computer resuming from suspend state"""
        logging.debug("System resumed from suspend")
        if not self.is_timer_running:
            # Close any existing alert dialog
            for child in self.children():
                if isinstance(child, QDialog):
                    child.close()
            # Reset the session alert timer
            self.reset_session_alert_timer()


def main():
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    app = QApplication(sys.argv)
    phrase = get_motivational_phrase()
    main_window = XbitoPomodoro(app, phrase)
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
