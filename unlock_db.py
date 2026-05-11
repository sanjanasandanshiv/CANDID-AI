# unlock_db.py
import sqlite3
import os
import time

db_path = 'hr_portal.db'

# Check if file exists
if not os.path.exists(db_path):
    print(f"Database {db_path} not found")
    exit()

# Try to connect and force close any connections
try:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = DELETE")
    conn.commit()
    conn.close()
    print("✅ Database unlocked")
except Exception as e:
    print(f"Error: {e}")

# Also check for -wal and -shm files and remove them if they exist
wal_file = db_path + "-wal"
shm_file = db_path + "-shm"

if os.path.exists(wal_file):
    try:
        os.remove(wal_file)
        print(f"✅ Removed {wal_file}")
    except:
        print(f"Could not remove {wal_file}")

if os.path.exists(shm_file):
    try:
        os.remove(shm_file)
        print(f"✅ Removed {shm_file}")
    except:
        print(f"Could not remove {shm_file}")