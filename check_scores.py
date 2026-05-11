# check_scores.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

# Check all applications with their resume scores
cursor.execute("""
    SELECT a.id, c.name, a.resume_score, a.status
    FROM applications a
    JOIN candidates c ON a.candidate_id = c.id
    ORDER BY a.resume_score DESC
""")

rows = cursor.fetchall()
print(f"Total applications: {len(rows)}")
print("-" * 60)
print(f"{'ID':<5} {'Name':<20} {'Score':<10} {'Status':<15}")
print("-" * 60)

for row in rows:
    score = row[2] if row[2] is not None else "NULL"
    print(f"{row[0]:<5} {row[1]:<20} {score:<10} {row[3]:<15}")

conn.close()