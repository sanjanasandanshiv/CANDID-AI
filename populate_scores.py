# set_test_scores.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

# Set scores for all applications (adjust based on your candidates)
# You can modify these values based on who you want to receive test links
cursor.execute("""
    UPDATE applications 
    SET resume_score = 85, 
        score_explanation = 'Manual score for testing - Candidate qualifies for test' 
    WHERE candidate_id IN (8, 9, 10, 13)
""")

cursor.execute("""
    UPDATE applications 
    SET resume_score = 75, 
        score_explanation = 'Manual score for testing - Candidate qualifies for test' 
    WHERE candidate_id IN (14, 15, 16)
""")

cursor.execute("""
    UPDATE applications 
    SET resume_score = 65, 
        score_explanation = 'Manual score for testing - Candidate qualifies for test' 
    WHERE candidate_id IN (17, 18, 19, 20)
""")

conn.commit()

# Verify the updates
cursor.execute("SELECT candidate_id, resume_score FROM applications")
rows = cursor.fetchall()
print("Updated scores:")
for row in rows:
    print(f"  Candidate {row[0]}: {row[1]}")

conn.close()