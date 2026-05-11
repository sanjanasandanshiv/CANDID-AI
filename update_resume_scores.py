# update_resume_scores.py
import sqlite3
import os
from app import extract_text_from_resume, score_resume, GEMINI_CLIENT

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

# Get all applications that don't have resume scores
cursor.execute("""
    SELECT a.id, a.candidate_id, a.job_id, c.resume_path, j.requirements
    FROM applications a
    JOIN candidates c ON a.candidate_id = c.id
    JOIN jobs j ON a.job_id = j.id
    WHERE a.resume_score IS NULL
""")
applications = cursor.fetchall()

print(f"Found {len(applications)} applications without resume scores")

updated = 0
failed = 0

for app in applications:
    app_id, candidate_id, job_id, resume_path, requirements = app
    
    if not resume_path:
        print(f"⚠️ No resume path for application {app_id}")
        failed += 1
        continue
    
    full_path = os.path.join('uploads', resume_path)
    
    if not os.path.exists(full_path):
        print(f"⚠️ Resume file not found: {full_path}")
        failed += 1
        continue
    
    # Extract text and score
    resume_text = extract_text_from_resume(full_path)
    if not resume_text:
        print(f"⚠️ Could not extract text from resume for app {app_id}")
        failed += 1
        continue
    
    score, rationale = score_resume(resume_text, requirements)
    
    # Update the database
    cursor.execute("""
        UPDATE applications 
        SET resume_score = ?, score_explanation = ? 
        WHERE id = ?
    """, (score, rationale, app_id))
    
    print(f"✅ App {app_id}: Score = {score}")
    updated += 1

conn.commit()
conn.close()

print(f"\nComplete! Updated: {updated}, Failed: {failed}")