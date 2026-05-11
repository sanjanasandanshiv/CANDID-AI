import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:")
for row in cursor.fetchall():
    print(row[0])

conn.close()