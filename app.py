import os
import sys
import logging

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QWidget,
)
from PySide6.QtCore import QTimer, Qt, QDate
from datetime import datetime, time

from MultiColorProgressBar import MultiColorProgressBar
from db import init_pomodoro_db, insert_pomodoro_session
from motivation import get_motivational_phrase

from sound import play_celebratory_melody, play_rest_end_melody


class XbitoPomodoro(QMainWindow):
    def __init__(self, app, phrase):
        self.phrase = phrase
        self.app = app
        self.start_time = None  # To store the session start time
        # Check if running in a debug session
        if (
            "TERM_PROGRAM" in os.environ.keys()
            and os.environ["TERM_PROGRAM"] == "vscode"
        ):
            logging.debug("Running in debug mode.")
            self.initial_seconds = 15  # 15 seconds for debug mode
            self.rest_seconds = 10  # 10 seconds for Rest timer in debug mode
            self.long_rest_seconds = 20  # 20 seconds for Long Rest timer in debug mode
        else:
            self.initial_seconds = 1800  # 30 minutes
            self.rest_seconds = 300  # 5 minutes for Rest timer
            self.long_rest_seconds = 900  # 15 minutes for Long Rest timer
        self.remaining_seconds = self.initial_seconds
        self.is_timer_running = False  # Track timer state
        # Initialize the database
        init_pomodoro_db()
        super().__init__()
        ## Window Setup
        self.setup_window()
        # Create a central widget and layout
        centralWidget = QWidget()
        self.layout = QVBoxLayout(centralWidget)
        self.setup_date_day_label()
        self.setup_progress_bar()
        self.update_progress_bar()
        self.setCentralWidget(centralWidget)
        # Update the progress bar and date/day label every minute
        self.setup_timer()
        # Create a label to display the timer type (Focus/Rest)
        self.setup_timer_type_label()
        # Create a horizontal layout for buttons and the countdown label
        self.setup_controls_layout()
        self.setup_start_pause_button()
        self.setup_emoticon_buttons()
        self.setup_motivational_phrase()
        self.apply_dark_theme()
        self.adjustSize()

    def setup_timer_type_label(self):
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
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress_bar)
        self.update_timer.start(60000)  # Update every minute
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_update_countdown)

    def setup_start_pause_button(self):
        self.start_pause_button = QPushButton("Start")
        self.start_pause_button.setStyleSheet("font-size: 18px; padding: 5px;")
        self.start_pause_button.clicked.connect(self.toggle_timer)
        self.layout.addWidget(self.start_pause_button)

        # Adding a Reset button
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet("font-size: 18px; padding: 5px;")
        self.reset_button.clicked.connect(self.reset_timer)
        self.layout.addWidget(self.reset_button)

    def setup_controls_layout(self):
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
        self.happy_button = QPushButton("😊")
        self.sad_button = QPushButton("😞")
        self.happy_button.clicked.connect(lambda: self.record_feedback("happy"))
        self.sad_button.clicked.connect(lambda: self.record_feedback("sad"))
        # Add emoticon buttons to the layout
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.happy_button)
        self.button_layout.addWidget(self.sad_button)
        self.layout.addLayout(self.button_layout)
        self.happy_button.setEnabled(False)
        self.sad_button.setEnabled(False)

    def setup_window(self):
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
        # Display motivational Phrase in the screen, allowing for multi-line if it exceeds the width
        self.motivational_phrase_label = QLabel(self.phrase)
        self.motivational_phrase_label.setWordWrap(True)  # Enable word wrapping
        self.motivational_phrase_label.setAlignment(Qt.AlignCenter)
        self.motivational_phrase_label.setStyleSheet(
            "font-size: 15px; font-weight: bold;"
        )
        self.layout.insertWidget(0, self.motivational_phrase_label)

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
            self.sad_button.setEnabled(True)
        else:
            # The button is currently the Start button
            self.timer.start(1000)  # Update every second
            self.start_pause_button.setText("Pause")
            self.happy_button.setEnabled(False)
            self.sad_button.setEnabled(False)
            # If timer type label is "Next: Rest", change it to "Rest" when starting the timer
            if self.timer_type_label.text() == "Next: Rest":
                self.timer_type_label.setText("Rest")
                self.timer_type = "Rest"
            elif self.timer_type_label.text() == "Next: Focus":
                self.timer_type_label.setText("Focus")
                self.timer_type = "Focus"

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
                self.sad_button.setEnabled(True)
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
        elif self.timer_type_label.text() == "Next: Focus":
            self.remaining_seconds = self.initial_seconds
        else:
            # Reset happened somewhere else, not at the end of a session, so reset to the Focus timer duration
            self.remaining_seconds = self.initial_seconds
        self.update_countdown_display()
        self.start_pause_button.setText("Start")
        self.is_timer_running = False
        self.happy_button.setEnabled(False)
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
            insert_pomodoro_session(self.start_time, end_time, feeling)
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
        """
        )

    def closeEvent(self, event):
        logging.debug("Application close event triggered. Resetting timer.")
        self.reset_timer()
        event.accept()  # Ensures the window closes smoothly


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
