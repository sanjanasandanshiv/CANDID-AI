import sqlite3
import os

DATABASE = 'hr_portal.db'

def setup_database():
    """Initializes and upgrades the HR Portal database to the final required schema."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        print(f"Checking database: {DATABASE}...")

        # 1. JOBS Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                requirements TEXT,
                deadline DATE NOT NULL,
                posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')

        # 2. CANDIDATES Table (Including profile_image_path and dob)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                address TEXT,
                dob TEXT,
                resume_path TEXT,
                profile_image_path TEXT,
                password_hash TEXT NOT NULL
            );
        ''')

        # 3. APPLICATIONS Table (Including status)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Applied',
                FOREIGN KEY (job_id) REFERENCES jobs (id),
                FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                UNIQUE(job_id, candidate_id) 
            );
        ''')

        # 4. MESSAGES Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id)
            );
        ''')

        # 5. TESTS Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL UNIQUE, 
                title TEXT NOT NULL,
                questions_json TEXT NOT NULL,   
                duration_minutes INTEGER NOT NULL,
                start_time DATETIME NOT NULL,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            );
        ''')

        # 6. TEST_RESULTS Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                submitted_answers_json TEXT,
                submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                FOREIGN KEY (job_id) REFERENCES jobs (id),
                UNIQUE (candidate_id, job_id)
            );
        ''')

        # 7. PROCTOR_LOGS Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS proctor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                job_id INTEGER NOT NULL,
                log_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            );
        ''')

        # --- SAFETY UPGRADE CHECK (For existing databases) ---
        # Add profile_image_path if it was missed in an old version
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN profile_image_path TEXT")
            print("- Added missing column: profile_image_path")
        except sqlite3.OperationalError:
            pass # Column already exists

        # Add dob if it was missed
        try:
            cursor.execute("ALTER TABLE candidates ADD COLUMN dob TEXT")
            print("- Added missing column: dob")
        except sqlite3.OperationalError:
            pass

        conn.commit()
        print("✅ Database setup and upgrades complete!")

    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    setup_database()