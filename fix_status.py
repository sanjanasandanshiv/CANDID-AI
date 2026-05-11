# fix_status.py
import sqlite3

conn = sqlite3.connect('hr_portal.db')
cursor = conn.cursor()

# Update all 'Test Sent' status to 'Selected for Test'
cursor.execute("""
    UPDATE applications 
    SET status = 'Selected for Test' 
    WHERE status = 'Test Sent'
""")

updated = cursor.rowcount
conn.commit()
conn.close()

print(f"✅ Updated {updated} applications from 'Test Sent' to 'Selected for Test'")
