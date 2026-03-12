import sqlite3
import os

# Path to your SQLite database file - use relative path from script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'instance', 'greensphere.db')

ALTERS = [
    "ALTER TABLE watering_reminders ADD COLUMN latitude FLOAT;",
    "ALTER TABLE watering_reminders ADD COLUMN longitude FLOAT;",
    "ALTER TABLE watering_reminders ADD COLUMN user_timezone VARCHAR(64);",
    "ALTER TABLE watering_reminders ADD COLUMN reminder_time VARCHAR(16);",
    "ALTER TABLE watering_reminders ADD COLUMN last_reminder_sent DATETIME;",
    "ALTER TABLE watering_reminders ADD COLUMN reminder_enabled BOOLEAN DEFAULT 1;"
]

def run_migration():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for sql in ALTERS:
        try:
            cursor.execute(sql)
            print(f"Success: {sql}")
        except sqlite3.OperationalError as e:
            print(f"Skipped: {sql} (Reason: {e})")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    run_migration()
