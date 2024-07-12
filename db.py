import sqlite3


def init_pomodoro_db():
    # Function to create/connect to a SQLite database and create the table if it doesn't exist
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS session_feedback
                 (start_time TEXT, end_time TEXT, feeling TEXT)"""
    )
    conn.commit()
    conn.close()


def insert_pomodoro_session(start_time, end_time, feeling):
    if not start_time:
        return  # Do not proceed if start_time is not set
    # Function to insert a session record into the database
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO session_feedback (start_time, end_time, feeling) VALUES (?, ?, ?)",
        (start_time, end_time, feeling),
    )
    conn.commit()
    conn.close()


def update_pomodoro_session(start_time, end_time, feeling):
    if not start_time:
        return  # Do not proceed if start_time is not set
    # Function to insert a session record into the database
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        "UPDATE session_feedback SET end_time = ?, feeling = ? WHERE start_time = ?",
        (end_time, feeling, start_time),
    )
    conn.commit()
    conn.close()
