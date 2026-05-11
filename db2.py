import sqlite3

def upgrade_soft_skills_db():
    conn = sqlite3.connect('hr_portal.db')
    # This table stores the evaluated metrics for the soft skills interview
    conn.execute('''
        CREATE TABLE IF NOT EXISTS soft_skills_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            job_id INTEGER NOT NULL,
            overall_score INTEGER,
            fluency_score INTEGER,
            grammar_score INTEGER,
            confidence_score INTEGER,
            relevance_score INTEGER,
            overall_explanation TEXT,
            question_details TEXT, -- JSON breakdown per question
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (candidate_id) REFERENCES candidates (id),
            FOREIGN KEY (job_id) REFERENCES jobs (id)
        )
    ''')
    conn.commit()
    conn.close()
    print("Soft skills table initialized.")

if __name__ == '__main__':
    upgrade_soft_skills_db()