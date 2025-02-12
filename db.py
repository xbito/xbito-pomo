import sqlite3
from datetime import datetime, timedelta

def get_db_version():
    """Get the current database version"""
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    try:
        c.execute("SELECT value FROM settings WHERE key = 'db_version'")
        version = c.fetchone()
        return int(version[0]) if version else 0
    except sqlite3.OperationalError:
        # If settings table doesn't exist, we're at version 0
        return 0
    finally:
        conn.close()

def run_migrations():
    """Run any pending database migrations"""
    current_version = get_db_version()
    
    if current_version < 1:
        # Migration to version 1: Remove feeling column and update schema
        conn = sqlite3.connect("pomodoro_sessions.db")
        c = conn.cursor()
        
        # Create new table without feeling column
        c.execute("""
            CREATE TABLE IF NOT EXISTS session_feedback_new
            (start_time TEXT, end_time TEXT)
        """)
        
        # Copy data from old table if it exists
        try:
            c.execute("""
                INSERT INTO session_feedback_new (start_time, end_time)
                SELECT start_time, end_time FROM session_feedback
            """)
        except sqlite3.OperationalError:
            # Old table might not exist, that's fine
            pass
            
        # Drop old table and rename new one
        c.execute("DROP TABLE IF EXISTS session_feedback")
        c.execute("ALTER TABLE session_feedback_new RENAME TO session_feedback")
        
        # Update version in settings
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings
            (key TEXT PRIMARY KEY, value INTEGER)
        """)
        c.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('db_version', 1)"
        )
        
        conn.commit()
        conn.close()

def init_db():
    """Initialize the database and run any pending migrations"""
    # Run migrations first
    run_migrations()
    
    # Then ensure all tables exist with current schema
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS session_feedback
                 (start_time TEXT, end_time TEXT)"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY, value INTEGER)"""
    )
    conn.commit()
    conn.close()

def insert_pomodoro_session(start_time, end_time, _unused):
    if not start_time:
        return  # Do not proceed if start_time is not set
    # Function to insert a session record into the database
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO session_feedback (start_time, end_time) VALUES (?, ?)",
        (start_time, end_time),
    )
    conn.commit()
    conn.close()


def update_pomodoro_session(start_time, end_time, _unused):
    if not start_time:
        return  # Do not proceed if start_time is not set
    # Function to update a session record in the database
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()
    c.execute(
        "UPDATE session_feedback SET end_time = ? WHERE start_time = ?",
        (end_time, start_time),
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


def fetch_yearly_daily_session_counts():
    """
    Returns a dictionary of { date_string (YYYY-MM-DD): session_count }
    for each day in the last 365 days.
    """
    conn = sqlite3.connect("pomodoro_sessions.db")
    c = conn.cursor()

    # Prepare a dict for all days in the last year, initialized with 0
    from datetime import datetime, timedelta

    today = datetime.now().date()
    daily_counts = {}
    for i in range(365):
        day = today - timedelta(days=i)
        daily_counts[day.strftime("%Y-%m-%d")] = 0

    # Count sessions per day
    c.execute(
        """
        SELECT DATE(start_time) as sdate, COUNT(*) as cnt
        FROM session_feedback
        WHERE DATE(start_time) >= DATE('now', '-365 day')
        GROUP BY DATE(start_time)
        """
    )
    for row in c.fetchall():
        if row[0] in daily_counts:
            daily_counts[row[0]] = row[1]

    conn.close()
    return daily_counts
