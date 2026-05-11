# # check_db_columns.py
# import sqlite3

# conn = sqlite3.connect('hr_portal.db')
# cursor = conn.cursor()

# # Get column info for applications table
# cursor.execute("PRAGMA table_info(applications)")
# columns = cursor.fetchall()

# print("Columns in 'applications' table:")
# print("-" * 40)
# for col in columns:
#     print(f"Column: {col[1]}, Type: {col[2]}")

# conn.close()















# quick_login_check.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

print("🔐 CANDIDATE LOGIN TABLE")
print("=" * 60)

# Show table structure
cursor.execute("PRAGMA table_info(candidates)")
print("\n📋 Table Structure:")
for col in cursor.fetchall():
    print(f"  • {col[1]} ({col[2]})")

# Show all candidates
cursor.execute("SELECT id, name, email, phone FROM candidates")
rows = cursor.fetchall()

print(f"\n📊 Total Candidates: {len(rows)}")
print("\nCandidate List:")
for row in rows:
    print(f"  ID: {row[0]}, Name: {row[1]}, Email: {row[2]}, Phone: {row[3]}")

conn.close()