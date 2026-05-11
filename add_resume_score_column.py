# add_resume_score_column.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE applications ADD COLUMN resume_score INTEGER")
    print("✅ Added resume_score column")
except Exception as e:
    print(f"Column may already exist: {e}")

conn.commit()
conn.close()