import sqlite3
from datetime import datetime, timedelta


def init_db():
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS session_feedback
                 (start_time TEXT, end_time TEXT, feeling TEXT)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value INTEGER)"""
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


def fetch_last_10_report_sessions():
    # Function to fetch the last 10 sessions from the database
    conn = sqlite3.connect("pomodoro_sessions.db")
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    c = conn.cursor()
    c.execute(
        "SELECT * FROM session_feedback WHERE end_time is not null ORDER BY start_time DESC LIMIT 10"
    )
    rows = c.fetchall()
    conn.close()
    # Convert rows to a list of dictionaries
    sessions = [dict(row) for row in rows]
    return sessions


def fetch_focus_summary():
    """
    Fetches a summary of Focus activity for the last week, yesterday, and today.
    """
    conn = sqlite3.connect("pomodoro_sessions.db")
    cursor = conn.cursor()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    week_ago = today - timedelta(days=7)

    # Query for the last week's average (excluding today)
    cursor.execute(
        """
        SELECT AVG(JULIANDAY(end_time) - JULIANDAY(start_time)) * 1440
        FROM session_feedback
        WHERE DATE(start_time) BETWEEN ? AND ?
        AND end_time is not null
    """,
        (week_ago, yesterday),
    )
    week_avg = cursor.fetchone()[0] or 0

    # Query for yesterday's total
    cursor.execute(
        """
        SELECT SUM(JULIANDAY(end_time) - JULIANDAY(start_time)) * 1440
        FROM session_feedback
        WHERE DATE(start_time) = ?
        AND end_time is not null
    """,
        (yesterday,),
    )
    yesterday_total = cursor.fetchone()[0] or 0

    # Query for today's total
    cursor.execute(
        """
        SELECT SUM(JULIANDAY(end_time) - JULIANDAY(start_time)) * 1440
        FROM session_feedback
        WHERE DATE(start_time) = ?
        AND end_time is not null
    """,
        (today,),
    )
    today_total = cursor.fetchone()[0] or 0

    conn.close()

    return {"week_avg": week_avg, "yesterday": yesterday_total, "today": today_total}


def save_setting(key, value):
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()


def get_setting(key, default_value):
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else default_value


def delete_setting(key):
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.commit()
    conn.close()
