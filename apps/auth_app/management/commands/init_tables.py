import os
import sqlite3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize local SQLite database tables to mirror Supabase schema'

    def handle(self, *args, **options):
        db_path = str(settings.BASE_DIR / 'db.sqlite3')
        self.stdout.write(f"Connecting to database at {db_path}...")
        
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 1. users
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            name TEXT,
            is_active BOOLEAN DEFAULT 1,
            linked_id TEXT
        )
        """)

        # 2. students
        cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            full_name TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            class_name TEXT,
            class_id TEXT,
            section TEXT,
            registration_no TEXT UNIQUE,
            registration_number TEXT,
            is_active BOOLEAN DEFAULT 1,
            attendance_pct REAL DEFAULT 0,
            attendance_percentage REAL DEFAULT 0,
            grade_avg REAL DEFAULT 0,
            grade_average REAL DEFAULT 0,
            risk_score REAL DEFAULT 0,
            risk_level TEXT DEFAULT 'green',
            gender TEXT,
            dob TEXT,
            parent_contact TEXT,
            parent_email TEXT,
            enrolled_date TEXT
        )
        """)

        # 3. faculty
        cur.execute("""
        CREATE TABLE IF NOT EXISTS faculty (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            employee_id TEXT UNIQUE,
            full_name TEXT,
            subject_specialization TEXT,
            contact_number TEXT,
            classes_assigned TEXT
        )
        """)

        # 4. classes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            class_name TEXT,
            faculty_id TEXT,
            subject TEXT,
            student_count INTEGER DEFAULT 0
        )
        """)

        # 5. attendance
        cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            date TEXT,
            subject_id TEXT,
            status TEXT,
            marked_by TEXT
        )
        """)

        # 6. grades
        cur.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            subject_id TEXT,
            subject TEXT,
            term TEXT,
            score REAL,
            total_score REAL DEFAULT 100,
            percentage REAL,
            month TEXT,
            class_name TEXT
        )
        """)

        # 7. assignments
        cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            class_name TEXT,
            subject TEXT,
            faculty_id TEXT,
            due_date TEXT,
            total_marks REAL,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT
        )
        """)

        # 8. assignment_submissions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS assignment_submissions (
            id TEXT PRIMARY KEY,
            assignment_id TEXT,
            student_id TEXT,
            student_name TEXT,
            status TEXT DEFAULT 'pending',
            marks_obtained REAL,
            feedback TEXT,
            submitted_at TEXT,
            created_at TEXT
        )
        """)

        # 9. risk_scores
        cur.execute("""
        CREATE TABLE IF NOT EXISTS risk_scores (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            score REAL,
            level TEXT,
            risk_level TEXT,
            reason TEXT,
            attendance_pct REAL,
            grade_avg REAL,
            grade_trend REAL,
            assignments_missed INTEGER,
            top_factors TEXT,
            calculated_at TEXT,
            created_at TEXT
        )
        """)

        # 10. interventions
        cur.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            student_name TEXT,
            faculty_id TEXT,
            teacher_name TEXT,
            action_type TEXT,
            notes TEXT,
            outcome TEXT,
            date TEXT,
            follow_up_date TEXT
        )
        """)

        # 11. fees
        cur.execute("""
        CREATE TABLE IF NOT EXISTS fees (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            student_name TEXT,
            class_name TEXT,
            amount_due REAL,
            amount_paid REAL DEFAULT 0,
            due_date TEXT,
            status TEXT DEFAULT 'pending',
            month TEXT
        )
        """)

        # 12. salaries
        cur.execute("""
        CREATE TABLE IF NOT EXISTS salaries (
            id TEXT PRIMARY KEY,
            faculty_id TEXT,
            faculty_name TEXT,
            designation TEXT,
            basic_salary REAL,
            allowances REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            net_salary REAL,
            month TEXT,
            year TEXT,
            status TEXT DEFAULT 'pending',
            paid_date TEXT
        )
        """)

        # 13. announcements
        cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id TEXT PRIMARY KEY,
            title TEXT,
            message TEXT,
            posted_by TEXT,
            posted_date TEXT,
            is_active BOOLEAN DEFAULT 1
        )
        """)

        # 14. audit_log
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            action TEXT,
            user_id TEXT,
            details TEXT,
            created_at TEXT
        )
        """)

        # 15. nlg_reports
        cur.execute("""
        CREATE TABLE IF NOT EXISTS nlg_reports (
            id TEXT PRIMARY KEY,
            student_id TEXT,
            report_text TEXT,
            month TEXT,
            created_at TEXT
        )
        """)

        # 16. enrollment_requests
        cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollment_requests (
            id TEXT PRIMARY KEY,
            student_name TEXT,
            father_name TEXT,
            email TEXT,
            phone TEXT,
            class_name TEXT,
            status TEXT DEFAULT 'pending',
            requested_at TEXT,
            reviewed_by TEXT,
            reviewed_at TEXT,
            rejection_reason TEXT
        )
        """)

        conn.commit()
        conn.close()
        self.stdout.write(self.style.SUCCESS("SQLite fallback tables initialized successfully."))
