import os
import sys
import logging
import threading

from time import sleep

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QSpinBox,
)
from PySide6.QtCore import QTimer, Qt, QDate, QEvent
from PySide6.QtGui import QAction

from datetime import datetime, time

from MultiColorProgressBar import MultiColorProgressBar
from db import (
    init_pomodoro_db,
    insert_pomodoro_session,
    update_pomodoro_session,
    fetch_last_10_report_sessions,
    fetch_focus_summary,  # Add this import
)
from motivation import get_motivational_phrase
from yoga import get_desk_yoga_stretch

from sound import play_celebratory_melody, play_rest_end_melody


class XbitoPomodoro(QMainWindow):
    def __init__(self, app, phrase):
        self.debug_mode = (
            "TERM_PROGRAM" in os.environ.keys()
            and os.environ["TERM_PROGRAM"] == "vscode"
        )
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
        else:
            self.initial_seconds = 1800  # 30 minutes
            self.rest_seconds = 300  # 5 minutes for Rest timer
            self.long_rest_seconds = 900  # 15 minutes for Long Rest timer
            self.update_motivational_phrase_seconds = 21600  # 6 hours
        self.sessions_before_long_rest = 2  # Number of sessions before a long rest
        self.completed_sessions = 0  # Track the number of completed sessions
        self.remaining_seconds = self.initial_seconds
        self.is_timer_running = False  # Track timer state
        # Initialize the database
        init_pomodoro_db()
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
        self.setup_menu()
        self.apply_dark_theme()
        self.adjustSize()

    def setup_menu(self):
        """
        Sets up the menu bar with the About and Settings actions.
        """
        menu_bar = self.menuBar()
        menu = menu_bar.addMenu("Menu")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(about_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings_dialog)
        menu.addAction(settings_action)

        report_action = QAction("Report", self)
        report_action.triggered.connect(self.show_report_dialog)
        menu.addAction(report_action)

        send_to_back_action = QAction("Send to Back", self)
        send_to_back_action.triggered.connect(self.send_to_back)
        menu.addAction(send_to_back_action)

    def show_report_dialog(self):
        """
        Displays a report Dialog with some basic reporting data.
        """
        # Create a QDialog object for the report dialog
        report_dialog = QDialog(self)
        report_dialog.setWindowTitle("Report")
        report_dialog.setMinimumWidth(550)  # Set a minimum width for the dialog
        report_dialog.setMinimumHeight(500)  # Set a minimum height for the dialog

        # Create a QVBoxLayout for the report dialog
        layout = QVBoxLayout()

        # Add a title and subtitle with a more sophisticated layout
        title_layout = QVBoxLayout()
        title_label = QLabel("<h1>Report</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        subtitle_label = QLabel("<p>Last 10 Sessions</p>")
        subtitle_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        layout.addLayout(title_layout)

        # Create a QTableWidget to display the report data
        table_widget = QTableWidget()
        table_widget.setColumnCount(3)
        table_widget.setHorizontalHeaderLabels(["Start Time", "End Time", "Feeling"])

        # Fetch the last 10 report sessions from the database
        report_sessions = fetch_last_10_report_sessions()

        # Populate the table with the report session details
        table_widget.setRowCount(len(report_sessions))
        for row, session in enumerate(report_sessions):
            start_time = QTableWidgetItem(session["start_time"])
            end_time = QTableWidgetItem(session["end_time"])
            feeling = QTableWidgetItem(str(session["feeling"]))

            table_widget.setItem(row, 0, start_time)
            table_widget.setItem(row, 1, end_time)
            table_widget.setItem(row, 2, feeling)

        # Set the table widget properties
        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_widget.setAlternatingRowColors(True)
        table_widget.setStyleSheet("QTableWidget { border: 1px solid #ddd; }")

        # Adjust column widths to fit the date-time columns
        table_widget.setColumnWidth(0, 200)  # Adjust width for "Start Time"
        table_widget.setColumnWidth(1, 200)  # Adjust width for "End Time"

        # Adjust row height to fit all rows within the dialog
        table_widget.verticalHeader().setDefaultSectionSize(30)  # Adjust row height

        # Add the table widget to the layout
        layout.addWidget(table_widget)

        # Add a close button with styling
        close_button = QPushButton("Close")
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        close_button.clicked.connect(report_dialog.accept)
        layout.addWidget(close_button)

        # Set the layout for the report dialog
        report_dialog.setLayout(layout)

        # Show the report dialog
        report_dialog.exec_()

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
        self.reset_button.clicked.connect(self.reset_timer)

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
        if not self.is_timer_running:
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.is_timer_running:
            # The button is currentlty the Pause button
            self.timer.stop()
            self.start_pause_button.setText("Start")
            self.happy_button.setEnabled(True)
            self.yoga_button.setEnabled(True)
            self.sad_button.setEnabled(True)
        else:
            # The button is currently the Start button
            self.timer.start(1000)  # Update every second
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

        self.is_timer_running = not self.is_timer_running

    def auto_update_countdown(self):
        """
        Automatically updates the countdown timer and handles actions when the timer reaches zero.

        Decreases the remaining seconds by 1 and updates the countdown label with the new time.
        If the remaining seconds reach zero:
        - stops the timer
        - changes the start/pause button text to "Start",
        - enables the feedback buttons
        - attempts to play a melody. If an error occurs while playing the melody, logs the error.

        """
        self.remaining_seconds -= 1
        self.update_countdown_display()
        if self.remaining_seconds <= 0:
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
            elif self.timer_type == "Rest":
                try:
                    play_rest_end_melody()
                except Exception as e:
                    logging.error(f"Error playing melody: {e}")
            # Set up the next timer
            if self.timer_type == "Focus":
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
                self.timer_type_label.setText("Next: Focus")
                self.remaining_seconds = self.initial_seconds
            # Convert self.remaining_seconds to minutes and seconds for the countdown label
            self.update_countdown_display()

    def reset_timer(self, from_feedback=False):
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
            self.reset_timer(from_feedback=True)

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
                background-color: #444444;
                color: #ffffff;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #22aa22;
                width: 20px; /* Used to increase chunk size */
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

    def show_dialog(self, title, text):
        """
        Displays a dialog with the specified title and text.

        Args:
            title (str): The title of the dialog.
            text (str): The text content of the dialog.

        """
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        dialog.setLayout(layout)
        dialog.exec()

    def show_about_dialog(self):
        """
        Displays an About dialog with information about the application.
        """
        about_text = """
        <h1>Xbito - Pomodoro Timer</h1>
        <p>Version 0.5</p>
        <p>Developed by <a href="https://github.com/xbito/">Xbito</a></p>
        <p>With help from GitHub Copilot</p>
        <p>Visit us at <a href="https://github.com/xbito/xbito-pomo">Github</a></p>
        """
        self.show_dialog("About", about_text)

    def show_settings_dialog(self):
        """
        Displays a Settings dialog with options to configure the application.
        """
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Settings")
        layout = QVBoxLayout()

        # Determine the unit (seconds or minutes) based on debug mode
        unit = "seconds" if self.debug_mode else "minutes"
        divisor = 1 if self.debug_mode else 60

        # Focus Duration
        focus_layout = QHBoxLayout()
        focus_label = QLabel(f"Focus Duration ({unit}):")
        self.focus_spinbox = QSpinBox()
        self.focus_spinbox.setRange(1, 7200 if self.debug_mode else 120)
        self.focus_spinbox.setValue(self.initial_seconds // divisor)
        focus_layout.addWidget(focus_label)
        focus_layout.addWidget(self.focus_spinbox)
        layout.addLayout(focus_layout)

        # Short Break Duration
        short_break_layout = QHBoxLayout()
        short_break_label = QLabel(f"Short Break Duration ({unit}):")
        self.short_break_spinbox = QSpinBox()
        self.short_break_spinbox.setRange(1, 1800 if self.debug_mode else 30)
        self.short_break_spinbox.setValue(self.rest_seconds // divisor)
        short_break_layout.addWidget(short_break_label)
        short_break_layout.addWidget(self.short_break_spinbox)
        layout.addLayout(short_break_layout)

        # Long Break Duration
        long_break_layout = QHBoxLayout()
        long_break_label = QLabel(f"Long Break Duration ({unit}):")
        self.long_break_spinbox = QSpinBox()
        self.long_break_spinbox.setRange(1, 3600 if self.debug_mode else 60)
        self.long_break_spinbox.setValue(self.long_rest_seconds // divisor)
        long_break_layout.addWidget(long_break_label)
        long_break_layout.addWidget(self.long_break_spinbox)
        layout.addLayout(long_break_layout)

        # Sessions before Long Break
        sessions_layout = QHBoxLayout()
        sessions_label = QLabel("Sessions before Long Break:")
        self.sessions_spinbox = QSpinBox()
        self.sessions_spinbox.setRange(1, 10)
        self.sessions_spinbox.setValue(self.sessions_before_long_rest)
        sessions_layout.addWidget(sessions_label)
        sessions_layout.addWidget(self.sessions_spinbox)
        layout.addLayout(sessions_layout)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(settings_dialog.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        settings_dialog.setLayout(layout)
        settings_dialog.exec()

    def save_settings(self):
        """
        Saves the settings from the dialog and updates the application state.
        """
        multiplier = 1 if self.debug_mode else 60

        self.initial_seconds = self.focus_spinbox.value() * multiplier
        self.rest_seconds = self.short_break_spinbox.value() * multiplier
        self.long_rest_seconds = self.long_break_spinbox.value() * multiplier
        self.sessions_before_long_rest = self.sessions_spinbox.value()

        # Update the remaining seconds if the timer is not running
        if not self.is_timer_running:
            if self.timer_type == "Focus":
                self.remaining_seconds = self.initial_seconds
            elif self.timer_type == "Rest":
                self.remaining_seconds = self.rest_seconds
            self.update_countdown_display()

        # Close the settings dialog
        self.sender().parent().accept()

    def closeEvent(self, event):
        logging.debug("Application close event triggered. Resetting timer.")
        self.reset_timer()
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
