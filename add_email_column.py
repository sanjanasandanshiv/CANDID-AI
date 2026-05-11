# add_email_column.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE candidates ADD COLUMN email TEXT")
    print("✅ Added email column to candidates table")
except Exception as e:
    print(f"Column may already exist: {e}")

conn.commit()
conn.close()