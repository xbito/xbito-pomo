def load_dark_theme():
    return """
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
    QLabel#dateLabel {
        font-size: 50px;
        font-weight: bold;
    }
    QLabel#monthLabel,
    QLabel#yearLabel,
    QLabel#dayLabel {
        font-size: 18px;
        font-weight: bold;
    }
    QLabel#motivationalPhraseLabel {
        font-size: 15px;
        font-weight: bold;
    }
    QLabel#countdownLabel {
        font-size: 24px;
    }
    QPushButton#startPauseButton,
    QPushButton#resetButton {
        font-size: 18px;
        padding: 5px;
    }
    QLabel#yearLabel {
        font-weight: normal; /* you had it not bold previously */
    }
    """
