from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QHeaderView,
    QPushButton,
    QSpinBox,
    QHBoxLayout,
    QWidget,
    QGridLayout,
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from db import (
    fetch_last_10_report_sessions,
    get_setting,
    save_setting,
    delete_setting,
    fetch_yearly_daily_session_counts,
)
from motivation import get_motivational_phrase


class AppMenu:
    def __init__(self, parent):
        self.parent = parent
        self.setup_menu()

    def setup_menu(self):
        menu_bar = self.parent.menuBar()
        menu = menu_bar.addMenu("Menu")

        about_action = QAction("About", self.parent)
        about_action.triggered.connect(self.show_about_dialog)
        menu.addAction(about_action)

        settings_action = QAction("Settings", self.parent)
        settings_action.triggered.connect(self.show_settings_dialog)
        menu.addAction(settings_action)

        report_action = QAction("Report", self.parent)
        report_action.triggered.connect(self.show_report_dialog)
        menu.addAction(report_action)

        send_to_back_action = QAction("Send to Back", self.parent)
        send_to_back_action.triggered.connect(self.parent.send_to_back)
        menu.addAction(send_to_back_action)

    def show_about_dialog(self):
        about_text = """
        <div style="font-family: Arial, sans-serif; padding: 10px;">
            <h1 style="color: #4CAF50; margin-bottom: 10px;">Xbito - Pomodoro Timer</h1>
            <p style="font-size: 16px;">Version 0.5</p>
            <p style="font-size: 16px;">
                Developed by
                <a href="https://github.com/xbito/"
                   style="color: #33dd33; text-decoration: none; font-weight: bold;">
                   Xbito
                </a>
            </p>
            <p style="font-size: 16px;">
                With help from
                <b>GitHub Copilot</b>
            </p>
            <p style="font-size: 16px;">
                Visit us at
                <a href="https://github.com/xbito/xbito-pomo"
                   style="color: #33dd33; text-decoration: none; font-weight: bold;">
                   GitHub
                </a>
            </p>
        </div>
        """
        self.parent.show_dialog("About", about_text)

    def show_settings_dialog(self):
        settings_dialog = QDialog(self.parent)
        settings_dialog.setWindowTitle("Settings")
        layout = QVBoxLayout()

        unit = "seconds" if self.parent.debug_mode else "minutes"
        divisor = 1 if self.parent.debug_mode else 60

        focus_layout = QHBoxLayout()
        focus_label = QLabel(f"Focus Duration ({unit}):")
        self.parent.focus_spinbox = QSpinBox()
        self.parent.focus_spinbox.setRange(1, 7200 if self.parent.debug_mode else 120)
        self.parent.focus_spinbox.setValue(self.parent.initial_seconds // divisor)
        focus_layout.addWidget(focus_label)
        focus_layout.addWidget(self.parent.focus_spinbox)
        layout.addLayout(focus_layout)

        short_break_layout = QHBoxLayout()
        short_break_label = QLabel(f"Short Break Duration ({unit}):")
        self.parent.short_break_spinbox = QSpinBox()
        self.parent.short_break_spinbox.setRange(
            1, 1800 if self.parent.debug_mode else 30
        )
        self.parent.short_break_spinbox.setValue(self.parent.rest_seconds // divisor)
        short_break_layout.addWidget(short_break_label)
        short_break_layout.addWidget(self.parent.short_break_spinbox)
        layout.addLayout(short_break_layout)

        long_break_layout = QHBoxLayout()
        long_break_label = QLabel(f"Long Break Duration ({unit}):")
        self.parent.long_break_spinbox = QSpinBox()
        self.parent.long_break_spinbox.setRange(
            1, 3600 if self.parent.debug_mode else 60
        )
        self.parent.long_break_spinbox.setValue(
            self.parent.long_rest_seconds // divisor
        )
        long_break_layout.addWidget(long_break_label)
        long_break_layout.addWidget(self.parent.long_break_spinbox)
        layout.addLayout(long_break_layout)

        sessions_layout = QHBoxLayout()
        sessions_label = QLabel("Sessions before Long Break:")
        self.parent.sessions_spinbox = QSpinBox()
        self.parent.sessions_spinbox.setRange(1, 10)
        self.parent.sessions_spinbox.setValue(self.parent.sessions_before_long_rest)
        sessions_layout.addWidget(sessions_label)
        sessions_layout.addWidget(self.parent.sessions_spinbox)
        layout.addLayout(sessions_layout)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.parent.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(settings_dialog.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        settings_dialog.setLayout(layout)
        settings_dialog.exec()

    def show_report_dialog(self):
        report_dialog = QDialog(self.parent)
        report_dialog.setWindowTitle("Report")
        report_dialog.setMinimumWidth(550)
        report_dialog.setMinimumHeight(500)

        layout = QVBoxLayout()
        title_layout = QVBoxLayout()
        title_label = QLabel("<h1>Report</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label_year = QLabel("<h2>Sessions in the last year</h2>")
        subtitle_label_year.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label_year)

        # Create a "contribution-like" grid widget
        daily_counts = fetch_yearly_daily_session_counts()

        # Find Monday on or before the day 12 months ago
        from datetime import datetime, timedelta

        today = datetime.now().date()
        start_date = today.replace(day=1) - timedelta(days=365)
        while start_date.weekday() != 0:  # 0 = Monday
            start_date -= timedelta(days=1)

        # Create "contribution-like" grid
        contrib_widget = QWidget()
        contrib_layout = QGridLayout(contrib_widget)
        contrib_layout.setSpacing(2)

        # Day labels at left for Monday, Wednesday, Friday
        day_labels = {0: "Mon", 2: "Wed", 4: "Fri"}

        # Fill chart up to today
        current = start_date
        col_index = 0
        last_month_shown = None

        while current <= today:
            week_of_year = (current - start_date).days // 7
            row = current.weekday()  # 0..6 for Mon..Sun
            if week_of_year != col_index:
                col_index = week_of_year
            # Label for day of week (left side)
            if row in day_labels and col_index == 0:
                label_day = QLabel(day_labels[row])
                contrib_layout.addWidget(label_day, row + 1, 0)
            # Month label on top if it's the first day (Monday) of a new month
            if row == 0:  # Monday
                month_label = current.strftime("%b")
                if month_label != last_month_shown:
                    lbl = QLabel(month_label)
                    lbl.setAlignment(Qt.AlignCenter)
                    contrib_layout.addWidget(lbl, 0, col_index + 1)
                    last_month_shown = month_label

            # Create the colored cell
            date_str = current.strftime("%Y-%m-%d")
            count = daily_counts.get(date_str, 0)
            shade = min(count, 5) * 40
            cell = QLabel()
            cell.setToolTip(f"{current.strftime('%B %d')}: {count}")
            cell.setStyleSheet(
                f"background-color: rgba(0, 200, 0, {shade});"
                "min-width: 10px; min-height: 10px;"
            )
            contrib_layout.addWidget(cell, row + 1, col_index + 1)
            current += timedelta(days=1)

        layout.addWidget(contrib_widget)

        subtitle_label_last_10 = QLabel("<h2>Last 10 Sessions details</h2>")
        subtitle_label_last_10.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label_last_10)

        table_widget = QTableWidget()
        table_widget.setColumnCount(3)
        table_widget.setHorizontalHeaderLabels(["Start Time", "End Time", "Feeling"])

        report_sessions = fetch_last_10_report_sessions()
        table_widget.setRowCount(len(report_sessions))
        for row, session in enumerate(report_sessions):
            start_time = QTableWidgetItem(session["start_time"])
            end_time = QTableWidgetItem(session["end_time"])
            feeling = QTableWidgetItem(str(session["feeling"]))

            table_widget.setItem(row, 0, start_time)
            table_widget.setItem(row, 1, end_time)
            table_widget.setItem(row, 2, feeling)

        table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_widget.setAlternatingRowColors(True)
        table_widget.setStyleSheet("QTableWidget { border: 1px solid #ddd; }")
        table_widget.setColumnWidth(0, 200)
        table_widget.setColumnWidth(1, 200)
        table_widget.verticalHeader().setDefaultSectionSize(30)

        layout.addWidget(table_widget)

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

        report_dialog.setLayout(layout)
        report_dialog.exec()
