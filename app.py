"""
LMS Admin Portal - Flask Application
Sample data driven (no database). In-memory Python lists/dicts act as the data store.
"""
import io
import copy
import json
import secrets
import re
from datetime import datetime, timedelta
import time
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_file
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "lms-admin-portal-secret-key-change-in-production"

# ---------------------------------------------------------------------------
# SAMPLE DATA STORE (in-memory, resets on restart)
# ---------------------------------------------------------------------------

INSTITUTIONS = [{"id": 1, "name": "My Institute", "code": "MYINST", "email": "admin@myinstitute.edu"}]

USERS = [
    {
        "id": 1,
        "name": "Admin User",
        "username": "admin",
        "email": "admin@myinstitute.edu",
        "password": generate_password_hash("admin123"),
        "role": "Admin",
    }
]

COURSES = [
    {"id": 1, "name": "Full Stack Web Development", "code": "FSWD-101", "category": "Development",
     "duration": "6 Months", "fee": 45000, "status": "Active",
     "description": "HTML, CSS, JS, React, Node.js and MongoDB from scratch to deployment."},
    {"id": 2, "name": "Data Science with Python", "code": "DSPY-201", "category": "Data Science",
     "duration": "5 Months", "fee": 55000, "status": "Active",
     "description": "Python, Pandas, NumPy, ML fundamentals and real-world projects."},
    {"id": 3, "name": "UI/UX Design Mastery", "code": "UIUX-110", "category": "Design",
     "duration": "3 Months", "fee": 30000, "status": "Active",
     "description": "Figma, design systems, prototyping and user research."},
    {"id": 4, "name": "Digital Marketing Pro", "code": "DMKT-140", "category": "Marketing",
     "duration": "4 Months", "fee": 25000, "status": "Inactive",
     "description": "SEO, SEM, social media and analytics-driven marketing."},
    {"id": 5, "name": "Cloud Computing with AWS", "code": "CLDA-220", "category": "Cloud",
     "duration": "4 Months", "fee": 40000, "status": "Active",
     "description": "EC2, S3, Lambda, DevOps pipelines and cloud architecture."},
]

TRAINERS = [
    {"id": 1, "name": "Arun Kumar", "email": "arun.kumar@myinstitute.edu", "phone": "9876500011",
     "specialization": "Full Stack Development", "experience": 8, "status": "Active"},
    {"id": 2, "name": "Priya Sharma", "email": "priya.sharma@myinstitute.edu", "phone": "9876500022",
     "specialization": "Data Science", "experience": 6, "status": "Active"},
    {"id": 3, "name": "Karthik Raja", "email": "karthik.raja@myinstitute.edu", "phone": "9876500033",
     "specialization": "UI/UX Design", "experience": 5, "status": "Active"},
    {"id": 4, "name": "Divya Menon", "email": "divya.menon@myinstitute.edu", "phone": "9876500044",
     "specialization": "Digital Marketing", "experience": 4, "status": "On Leave"},
    {"id": 5, "name": "Suresh Babu", "email": "suresh.babu@myinstitute.edu", "phone": "9876500055",
     "specialization": "Cloud Computing", "experience": 9, "status": "Active"},
]

BATCHES = [
    {"id": 1, "name": "FSWD Morning Batch A", "course_id": 1, "trainer_id": 1, "start_date": "2026-01-10",
     "end_date": "2026-07-10", "timing": "8:00 AM - 10:00 AM", "status": "Ongoing", "capacity": 30, "enrolled": 26},
    {"id": 2, "name": "DSPY Evening Batch B", "course_id": 2, "trainer_id": 2, "start_date": "2026-02-01",
     "end_date": "2026-07-01", "timing": "6:00 PM - 8:00 PM", "status": "Ongoing", "capacity": 25, "enrolled": 22},
    {"id": 3, "name": "UIUX Weekend Batch C", "course_id": 3, "trainer_id": 3, "start_date": "2026-03-15",
     "end_date": "2026-06-15", "timing": "10:00 AM - 1:00 PM", "status": "Upcoming", "capacity": 20, "enrolled": 12},
    {"id": 4, "name": "DMKT Morning Batch D", "course_id": 4, "trainer_id": 4, "start_date": "2025-09-01",
     "end_date": "2026-01-01", "timing": "9:00 AM - 11:00 AM", "status": "Completed", "capacity": 25, "enrolled": 25},
    {"id": 5, "name": "CLDA Evening Batch E", "course_id": 5, "trainer_id": 5, "start_date": "2026-04-05",
     "end_date": "2026-08-05", "timing": "7:00 PM - 9:00 PM", "status": "Upcoming", "capacity": 20, "enrolled": 8},
]

GUARDIANS = [
    {"id": 1, "name": "Ramesh Iyer", "relation": "Father", "phone": "9840011122",
     "email": "ramesh.iyer@gmail.com", "student_id": 1, "address": "12 Gandhi Street, Coimbatore"},
    {"id": 2, "name": "Lakshmi Nair", "relation": "Mother", "phone": "9840022233",
     "email": "lakshmi.nair@gmail.com", "student_id": 2, "address": "45 Anna Nagar, Chennai"},
    {"id": 3, "name": "Venkatesh Rao", "relation": "Father", "phone": "9840033344",
     "email": "venkatesh.rao@gmail.com", "student_id": 3, "address": "8 MG Road, Bengaluru"},
    {"id": 4, "name": "Sunitha Reddy", "relation": "Mother", "phone": "9840044455",
     "email": "sunitha.reddy@gmail.com", "student_id": 4, "address": "23 Jubilee Hills, Hyderabad"},
    {"id": 5, "name": "Manoj Pillai", "relation": "Father", "phone": "9840055566",
     "email": "manoj.pillai@gmail.com", "student_id": 5, "address": "67 Marine Drive, Kochi"},
]

STUDENTS = [
    {"id": 1, "name": "Aravind Iyer", "email": "aravind.iyer@gmail.com", "phone": "9900011122",
     "course_id": 1, "batch_id": 1, "enrollment_date": "2026-01-08", "status": "Active", "guardian_id": 1},
    {"id": 2, "name": "Sneha Nair", "email": "sneha.nair@gmail.com", "phone": "9900022233",
     "course_id": 2, "batch_id": 2, "enrollment_date": "2026-01-28", "status": "Active", "guardian_id": 2},
    {"id": 3, "name": "Rahul Rao", "email": "rahul.rao@gmail.com", "phone": "9900033344",
     "course_id": 3, "batch_id": 3, "enrollment_date": "2026-03-10", "status": "Active", "guardian_id": 3},
    {"id": 4, "name": "Anjali Reddy", "email": "anjali.reddy@gmail.com", "phone": "9900044455",
     "course_id": 4, "batch_id": 4, "enrollment_date": "2025-08-25", "status": "Inactive", "guardian_id": 4},
    {"id": 5, "name": "Vishnu Pillai", "email": "vishnu.pillai@gmail.com", "phone": "9900055566",
     "course_id": 5, "batch_id": 5, "enrollment_date": "2026-04-01", "status": "Active", "guardian_id": 5},
    {"id": 6, "name": "Meera Krishnan", "email": "meera.krishnan@gmail.com", "phone": "9900066677",
     "course_id": 1, "batch_id": 1, "enrollment_date": "2026-01-09", "status": "Active", "guardian_id": 1},
    {"id": 7, "name": "Kiran Kumar", "email": "kiran.kumar@gmail.com", "phone": "9900077788",
     "course_id": 2, "batch_id": 2, "enrollment_date": "2026-01-29", "status": "Active", "guardian_id": 2},
]

# Support multiple course enrollments while keeping the original primary course_id for batch/session compatibility.
for _student in STUDENTS:
    if not _student.get("course_ids"):
        _student["course_ids"] = [_student.get("course_id")] if _student.get("course_id") else []


ATTENDANCE = [
    {"id": 1, "student_id": 1, "batch_id": 1, "date": "2026-09-15", "status": "Present"},
    {"id": 2, "student_id": 1, "batch_id": 1, "date": "2026-09-16", "status": "Present"},
    {"id": 3, "student_id": 1, "batch_id": 1, "date": "2026-09-17", "status": "Absent"},
    {"id": 4, "student_id": 2, "batch_id": 2, "date": "2026-09-15", "status": "Present"},
    {"id": 5, "student_id": 2, "batch_id": 2, "date": "2026-09-16", "status": "Late"},
    {"id": 6, "student_id": 3, "batch_id": 3, "date": "2026-09-15", "status": "Present"},
    {"id": 7, "student_id": 4, "batch_id": 4, "date": "2026-09-15", "status": "Absent"},
    {"id": 8, "student_id": 5, "batch_id": 5, "date": "2026-09-15", "status": "Present"},
    {"id": 9, "student_id": 6, "batch_id": 1, "date": "2026-09-15", "status": "Present"},
    {"id": 10, "student_id": 7, "batch_id": 2, "date": "2026-09-15", "status": "Late"},
]

LIVE_ATTENDANCE = {}  # (student_id, session_id) -> live connection state

SESSIONS = [
    {"id": 1, "topic": "Introduction to React Hooks", "batch_id": 1, "trainer_id": 1,
     "date": "2026-09-25", "time": "08:00 AM", "duration": "2 Hours", "status": "Scheduled"},
    {"id": 2, "topic": "Pandas DataFrame Deep Dive", "batch_id": 2, "trainer_id": 2,
     "date": "2026-09-26", "time": "06:00 PM", "duration": "2 Hours", "status": "Scheduled"},
    {"id": 3, "topic": "Figma Component Systems", "batch_id": 3, "trainer_id": 3,
     "date": "2026-09-24", "time": "10:00 AM", "duration": "3 Hours", "status": "Completed"},
    {"id": 4, "topic": "AWS Lambda & Serverless", "batch_id": 5, "trainer_id": 5,
     "date": "2026-09-28", "time": "07:00 PM", "duration": "2 Hours", "status": "Scheduled"},
    {"id": 5, "topic": "REST API Design Principles", "batch_id": 1, "trainer_id": 1,
     "date": "2026-09-22", "time": "08:00 AM", "duration": "2 Hours", "status": "Cancelled"},
]

ASSESSMENTS = [
    {"id": 1, "title": "JavaScript Fundamentals Quiz", "type": "Quiz", "course_id": 1, "batch_id": 1,
     "date": "2026-09-30", "max_marks": 20, "status": "Scheduled"},
    {"id": 2, "title": "Python for Data Science - Mid Term", "type": "Exam", "course_id": 2, "batch_id": 2,
     "date": "2026-10-05", "max_marks": 100, "status": "Scheduled"},
    {"id": 3, "title": "Portfolio Redesign Assignment", "type": "Assignment", "course_id": 3, "batch_id": 3,
     "date": "2026-09-20", "max_marks": 50, "status": "Completed"},
    {"id": 4, "title": "Capstone Marketing Campaign", "type": "Project", "course_id": 4, "batch_id": 4,
     "date": "2025-12-20", "max_marks": 100, "status": "Completed"},
    {"id": 5, "title": "AWS Cloud Architecture Exam", "type": "Exam", "course_id": 5, "batch_id": 5,
     "date": "2026-10-10", "max_marks": 100, "status": "Scheduled"},
]

ASSESSMENT_MARKS = []

ANNOUNCEMENTS = [
    {"id": 1, "title": "Diwali Holiday Notice", "message": "The institute will remain closed from Oct 20-22 for Diwali.",
     "date": "2026-09-18", "audience": "All", "priority": "High"},
    {"id": 2, "title": "New Batch for Cloud Computing", "message": "Admissions open for the new AWS batch starting October.",
     "date": "2026-09-16", "audience": "Students", "priority": "Medium"},
    {"id": 3, "title": "Trainer Meeting Scheduled", "message": "Monthly trainer sync-up on Sept 29 at 5 PM.",
     "date": "2026-09-20", "audience": "Trainers", "priority": "Medium"},
    {"id": 4, "title": "Fee Payment Reminder", "message": "Please clear pending fee dues before Sept 30 to avoid late fee.",
     "date": "2026-09-19", "audience": "Students", "priority": "High"},
]

PAYMENTS = [
    {"id": 1, "student_id": 1, "amount": 45000, "date": "2026-01-08", "method": "UPI", "status": "Paid", "invoice_no": "INV-1001"},
    {"id": 2, "student_id": 2, "amount": 55000, "date": "2026-01-28", "method": "Card", "status": "Paid", "invoice_no": "INV-1002"},
    {"id": 3, "student_id": 3, "amount": 15000, "date": "2026-03-10", "method": "Bank Transfer", "status": "Pending", "invoice_no": "INV-1003"},
    {"id": 4, "student_id": 4, "amount": 25000, "date": "2025-08-25", "method": "Cash", "status": "Failed", "invoice_no": "INV-1004"},
    {"id": 5, "student_id": 5, "amount": 40000, "date": "2026-04-01", "method": "UPI", "status": "Paid", "invoice_no": "INV-1005"},
    {"id": 6, "student_id": 6, "amount": 45000, "date": "2026-01-09", "method": "Card", "status": "Pending", "invoice_no": "INV-1006"},
    {"id": 7, "student_id": 7, "amount": 55000, "date": "2026-01-29", "method": "UPI", "status": "Paid", "invoice_no": "INV-1007"},
]

MATERIALS = [
    {"id": 1, "title": "React Hooks Notes", "description": "Trainer notes and examples for the React Hooks module.", "course_id": 1, "batch_id": 1, "type": "PDF", "url": "#", "date": "2026-09-18", "uploaded_by": "Arun Kumar"},
    {"id": 2, "title": "Python Pandas Practice Sheet", "description": "Practice material for DataFrame operations and analysis.", "course_id": 2, "batch_id": 2, "type": "Document", "url": "#", "date": "2026-09-17", "uploaded_by": "Priya Sharma"},
]

FORUM_POSTS = [
    {"id": 1, "title": "Welcome to the Discussion Forum", "message": "Use this space for course doubts, ideas, announcements and peer discussion.", "author": "Institute Admin", "role": "admin", "date": "2026-09-20 10:00"},
    {"id": 2, "title": "React Hooks Doubt", "message": "Can someone explain when to use useMemo and useCallback?", "author": "Arun Kumar", "role": "trainer", "date": "2026-09-21 16:30"},
]

DATA = {
    "courses": COURSES, "trainers": TRAINERS, "batches": BATCHES, "students": STUDENTS,
    "guardians": GUARDIANS, "attendance": ATTENDANCE, "sessions": SESSIONS,
    "assessments": ASSESSMENTS, "assessment_marks": ASSESSMENT_MARKS, "announcements": ANNOUNCEMENTS, "payments": PAYMENTS, "materials": MATERIALS, "forum_posts": FORUM_POSTS,
}
for _s in SESSIONS:
    _s.setdefault("meeting_link", "https://meet.jit.si/MyInstitute-Session-"+str(_s["id"]))
    _s.setdefault("recording_url", "")


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def next_id(items):
    return (max((i["id"] for i in items), default=0)) + 1


def find_by_id(items, item_id):
    return next((i for i in items if i["id"] == item_id), None)


def student_course_ids(student):
    ids = list(student.get("course_ids") or [])
    ids += [e.get("course_id") for e in (student.get("enrollments") or []) if e.get("course_id")]
    if not ids and student.get("course_id"):
        ids = [student.get("course_id")]
    return list(dict.fromkeys([i for i in ids if i]))

def student_enrollments(student):
    if not student:
        return []
    rows = student.get("enrollments") or []
    if rows:
        return rows
    if student.get("course_id"):
        return [{"course_id": student.get("course_id"), "batch_id": student.get("batch_id"), "enrollment_date": student.get("enrollment_date"), "status": student.get("status", "Active")}]
    return []

def student_course_names(student):
    return [course_name(cid) for cid in student_course_ids(student) if find_by_id(COURSES, cid)]

def course_name(cid):
    c = find_by_id(COURSES, cid)
    return c["name"] if c else "—"


def trainer_name(tid):
    t = find_by_id(TRAINERS, tid)
    return t["name"] if t else "—"


def batch_name(bid):
    b = find_by_id(BATCHES, bid)
    return b["name"] if b else "—"


def student_name(sid):
    s = find_by_id(STUDENTS, sid)
    return s["name"] if s else "—"


def assessment_by_id(assessment_id):
    return next((a for a in ASSESSMENTS if a.get("id")==assessment_id and a.get("institution_id",1)==current_institution_id()), None)

def assessment_mark(assessment_id, student_id):
    return next((m for m in ASSESSMENT_MARKS if m.get("assessment_id")==assessment_id and m.get("student_id")==student_id and m.get("institution_id",1)==current_institution_id()), None)

def parse_duration_minutes(value):
    """Convert session duration labels such as '2 Hours' or '90 Minutes' to minutes."""
    if value is None:
        return 0
    text = str(value).strip().lower()
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if not m:
        return 0
    amount = float(m.group(1))
    if "hour" in text or text.endswith("h"):
        return max(1, round(amount * 60))
    return max(1, round(amount))

def live_attendance_key(student_id, session_id):
    return (int(student_id), int(session_id))

def finalize_live_attendance(student_id, session_id):
    key = live_attendance_key(student_id, session_id)
    state = LIVE_ATTENDANCE.get(key)
    if not state:
        return None
    now = time.time()
    if state.get("connected") and state.get("last_heartbeat"):
        state["active_seconds"] += max(0, min(now - state["last_heartbeat"], 30))
    state["connected"] = False
    state["last_heartbeat"] = now
    duration_seconds = max(60, state.get("duration_minutes", 1) * 60)
    required_seconds = duration_seconds * 0.75
    eligible = state.get("active_seconds", 0) >= required_seconds
    existing = next((a for a in ATTENDANCE if a.get("session_id") == session_id and a.get("student_id") == student_id), None)
    session_item = next((x for x in SESSIONS if x.get("id") == session_id), None)
    batch_id = session_item.get("batch_id") if session_item else state.get("batch_id")
    date_value = session_item.get("date") if session_item else time.strftime("%Y-%m-%d")
    record = {
        "student_id": student_id, "batch_id": batch_id, "date": date_value,
        "status": "Present" if eligible else "Absent", "session_id": session_id,
        "active_minutes": round(state.get("active_seconds", 0) / 60, 1),
        "required_minutes": round(required_seconds / 60, 1), "auto_tracked": True,
        "institution_id": current_institution_id()
    }
    if existing:
        existing.update(record)
        existing["id"] = existing.get("id")
    else:
        record["id"] = max([a.get("id",0) for a in ATTENDANCE] or [0]) + 1
        ATTENDANCE.append(record)
    return {"eligible": eligible, "active_minutes": record["active_minutes"], "required_minutes": record["required_minutes"], "status": record["status"]}

def attendance_percentage(student_id):
    records = [a for a in ATTENDANCE if a["student_id"] == student_id]
    if not records:
        return 0
    present = len([a for a in records if a["status"] in ("Present", "Late")])
    return round((present / len(records)) * 100)


app.jinja_env.globals.update(
    course_name=course_name, trainer_name=trainer_name, batch_name=batch_name,
    student_name=student_name, attendance_percentage=attendance_percentage, student_course_names=student_course_names, student_enrollments=student_enrollments, assessment_mark=assessment_mark, assessment_by_id=assessment_by_id,
)

# ---------------------------------------------------------------------------
# POSTGRESQL DATABASE LAYER
# ---------------------------------------------------------------------------
# All persistent LMS data is stored in PostgreSQL.  The existing route layer
# continues to use Python dicts for rendering/compatibility, but those dicts
# are loaded from and persisted to PostgreSQL rather than SQLite/files.
import os
from dotenv import load_dotenv

load_dotenv()

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lms")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

DB_POOL = ConnectionPool(
    conninfo=DATABASE_URL,
    min_size=int(os.getenv("DB_POOL_MIN", "2")),
    max_size=int(os.getenv("DB_POOL_MAX", "20")),
    kwargs={"row_factory": dict_row},
    open=True,
)

class PGConnection:
    """Small compatibility wrapper for the old route code."""
    def __init__(self, conn):
        self.conn = conn
    def execute(self, sql, params=()):
        # Existing code used SQLite's '?' placeholders; translate them for psycopg.
        sql = sql.replace("?", "%s")
        return self.conn.execute(sql, params)
    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self): DB_POOL.putconn(self.conn)

def get_db():
    return PGConnection(DB_POOL.getconn())

def init_db():
    con = get_db()
    try:
        con.execute("""
            CREATE TABLE IF NOT EXISTS institutions (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                code VARCHAR(80) NOT NULL UNIQUE,
                email VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                username VARCHAR(120) NOT NULL,
                email VARCHAR(255),
                password TEXT NOT NULL,
                role VARCHAR(30) NOT NULL,
                institution_id BIGINT NOT NULL REFERENCES institutions(id),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(institution_id, username),
                UNIQUE(institution_id, email)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS ix_users_institution_role ON users(institution_id, role)")
        con.execute("""
            CREATE TABLE IF NOT EXISTS records (
                entity VARCHAR(80) NOT NULL,
                id BIGINT NOT NULL,
                institution_id BIGINT NOT NULL REFERENCES institutions(id),
                payload JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY(entity, id)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS ix_records_institution_entity ON records(institution_id, entity)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_records_entity_updated ON records(entity, updated_at DESC)")
        # Normalized high-volume tables used by attendance/enrollment/reporting.
        con.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id BIGSERIAL PRIMARY KEY,
                institution_id BIGINT NOT NULL REFERENCES institutions(id),
                student_id BIGINT NOT NULL,
                course_id BIGINT NOT NULL,
                batch_id BIGINT NOT NULL,
                status VARCHAR(30) DEFAULT 'Active',
                enrolled_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(institution_id, student_id, course_id)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_student ON enrollments(institution_id, student_id)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_batch ON enrollments(institution_id, batch_id)")
        con.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records (
                id BIGSERIAL PRIMARY KEY,
                institution_id BIGINT NOT NULL REFERENCES institutions(id),
                student_id BIGINT NOT NULL,
                batch_id BIGINT,
                session_id BIGINT,
                attendance_date DATE,
                active_seconds INTEGER DEFAULT 0,
                required_seconds INTEGER DEFAULT 0,
                status VARCHAR(20),
                auto_tracked BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(institution_id, student_id, session_id)
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS ix_attendance_student_date ON attendance_records(institution_id, student_id, attendance_date)")
        con.execute("CREATE INDEX IF NOT EXISTS ix_attendance_session ON attendance_records(institution_id, session_id, student_id)")

        con.execute("INSERT INTO institutions(id,name,code,email) VALUES(1,'My Institute','MYINST','admin@myinstitute.edu') ON CONFLICT (id) DO NOTHING")
        # Seed demo accounts only when the database is empty.
        if not con.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            con.execute("""
                INSERT INTO users(name,username,email,password,role,institution_id)
                VALUES(%s,%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s,%s),(%s,%s,%s,%s,%s,%s)
            """, (
                "Institute Admin","admin","admin@myinstitute.edu",generate_password_hash("admin123"),"admin",1,
                "Trainer","trainer","trainer@myinstitute.edu",generate_password_hash("trainer123"),"trainer",1,
                "Student","student","student@myinstitute.edu",generate_password_hash("student123"),"student",1,
            ))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def load_entity(entity):
    con = get_db()
    try:
        rows = con.execute("SELECT payload FROM records WHERE entity=%s ORDER BY id", (entity,)).fetchall()
        return [dict(r["payload"]) for r in rows]
    finally:
        con.close()


def save_entity(entity, items):
    """Persist an entity collection in one PostgreSQL transaction.

    Upserts are batched and removed IDs are deleted.  No SQLite file or
    application-local persistence is used.
    """
    con = get_db()
    try:
        normalized = []
        for item in items:
            item = dict(item)
            iid = int(item.get("institution_id") or 1)
            item["institution_id"] = iid
            normalized.append(
                (entity, int(item["id"]), iid, json.dumps(item))
            )

        if normalized:
            # Psycopg 3 uses executemany() on a cursor, not on the connection.
            with con.conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO records(entity,id,institution_id,payload,updated_at)
                    VALUES(%s,%s,%s,%s::jsonb,NOW())
                    ON CONFLICT(entity,id) DO UPDATE SET
                        institution_id=EXCLUDED.institution_id,
                        payload=EXCLUDED.payload,
                        updated_at=NOW()
                """, normalized)

            ids = [x[1] for x in normalized]
            con.execute(
                "DELETE FROM records WHERE entity=%s AND id <> ALL(%s)",
                (entity, ids)
            )
        else:
            con.execute(
                "DELETE FROM records WHERE entity=%s",
                (entity,)
            )

        # Keep normalized high-volume tables in sync for reporting/indexing.
        if entity == "enrollments":
            pass

        elif entity == "attendance":
            for item in items:
                con.execute("""
                    INSERT INTO attendance_records(
                        institution_id,student_id,batch_id,session_id,attendance_date,
                        active_seconds,required_seconds,status,auto_tracked
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(institution_id,student_id,session_id) DO UPDATE SET
                        batch_id=EXCLUDED.batch_id,
                        attendance_date=EXCLUDED.attendance_date,
                        active_seconds=EXCLUDED.active_seconds,
                        required_seconds=EXCLUDED.required_seconds,
                        status=EXCLUDED.status,
                        auto_tracked=EXCLUDED.auto_tracked
                """, (
                    item.get("institution_id", 1),
                    item.get("student_id"),
                    item.get("batch_id"),
                    item.get("session_id"),
                    item.get("date") or None,
                    int(float(
                        item.get("active_seconds")
                        or float(item.get("active_minutes") or 0) * 60
                    )),
                    int(float(
                        item.get("required_seconds")
                        or float(item.get("required_minutes") or 0) * 60
                    )),
                    item.get("status"),
                    bool(item.get("auto_tracked", False))
                ))

        con.commit()

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()


def save_enrollment_record(institution_id, student_id, course_id, batch_id, status="Active", enrolled_at=None):
    """Persist enrollment in a normalized PostgreSQL table for fast joins/reports."""
    con = get_db()
    try:
        con.execute("""
            INSERT INTO enrollments(institution_id,student_id,course_id,batch_id,status,enrolled_at)
            VALUES(%s,%s,%s,%s,%s,%s)
            ON CONFLICT(institution_id,student_id,course_id) DO UPDATE SET
                batch_id=EXCLUDED.batch_id,status=EXCLUDED.status,enrolled_at=EXCLUDED.enrolled_at
        """, (institution_id, student_id, course_id, batch_id, status, enrolled_at or datetime.now()))
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

def replace_data_from_db():
    for entity in DATA:
        DATA[entity][:] = load_entity(entity)

def ensure_seed_records():
    # Seed the demo collections only if their PostgreSQL entity is empty.
    for entity, items in DATA.items():
        if not load_entity(entity):
            for item in items:
                item.setdefault("institution_id", 1)
            save_entity(entity, items)

# Initialize PostgreSQL schema and load persistent data.
init_db()
ensure_seed_records()
replace_data_from_db()
for _entity in DATA:
    for _item in DATA[_entity]: _item.setdefault("institution_id", 1)
for _pmt in PAYMENTS:
    if _pmt.get("status") == "Pending": _pmt["status"] = "Failed"
save_entity("payments", PAYMENTS)
for _g in GUARDIANS:
    _g.pop("email", None)
save_entity("guardians", GUARDIANS)

def allowed(role, endpoint):
    """Role-based page access.
    Admin: full institute access.
    Trainer: assigned courses/batches/students/guardians/materials/attendance/
             assessments/sessions plus home, dashboard and discussion.
    Student+Parent: only personal learning/financial/session information.
    """
    if role == "admin":
        return True
    if role == "trainer":
        return endpoint in {
            "dashboard", "courses_page", "students_page", "attendance_page",
            "announcements_page", "assessments_page", "reports_page", "sessions_page",
            "recordings_page", "discussion_forum", "export_report", "student_report_pdf", "logout"
        }
    if role == "student":
        return endpoint in {
            "dashboard", "courses_page", "attendance_page", "announcements_page",
            "assessments_page", "reports_page",
            "sessions_page", "recordings_page", "discussion_forum", "export_report", "student_report_pdf", "logout"
        }
    return False

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session: return redirect(url_for("login"))
        if not allowed(session.get("user_role"), request.endpoint):
            flash("You do not have access to this section.", "error")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return wrapper

@app.route("/", methods=["GET"])
def index():
    return redirect(url_for("dashboard") if "user_id" in session else url_for("login"))

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    return role_login("admin")

@app.route("/trainer-login", methods=["GET", "POST"])
def trainer_login():
    return role_login("trainer")

@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    return role_login("student")

@app.route("/login/<role>", methods=["GET","POST"])
def role_login(role):
    if role not in {"admin","trainer","student"}: return redirect(url_for("login"))
    if request.method == "POST":
        identifier=request.form.get("username","").strip(); password=request.form.get("password","")
        con=get_db(); u=con.execute("SELECT * FROM users WHERE role=? AND (username=? OR email=?)",(role,identifier,identifier)).fetchone(); con.close()
        if u and check_password_hash(u["password"],password):
            session["user_id"]=u["id"]; session["user_name"]=u["name"]; session["user_role"]=u["role"]; session["user_email"]=u["email"]; session["institution_id"]=u["institution_id"] or 1
            if role == "student":
                st = next((x for x in STUDENTS if str(x.get("email","")).strip().lower() == str(u["email"] or "").strip().lower() and x.get("institution_id",1) == (u["institution_id"] or 1)), None)
                if st: session["student_id"] = st.get("id")
            return redirect(url_for("home" if role == "admin" else "dashboard"))
        flash("Invalid username or password.","error")
    labels={"admin":"Institute Admin","trainer":"Trainer","student":"Student + Parent"}
    return render_template("role_login.html", role=role, role_label=labels[role])

@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/register/<role>", methods=["GET","POST"])
def register_role(role):
    labels={"admin":"Institute Admin","trainer":"Trainer","student":"Student + Parent"}
    if role not in labels:
        return redirect(url_for("register"))

    if request.method == "POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        username=request.form.get("username","").strip()
        password=request.form.get("password","")
        institution_name=request.form.get("institution_name","").strip()
        institution_code=request.form.get("institution_code","").strip().upper()

        # Basic validation before touching the database.
        if not name or not email or not username or not password or not institution_code:
            flash("Please fill in all required fields.","error")
            return render_template("register_role.html", role=role, role_label=labels[role])
        if len(password) < 6:
            flash("Password must contain at least 6 characters.","error")
            return render_template("register_role.html", role=role, role_label=labels[role])
        if role == "admin" and not institution_name:
            flash("Institute name is required.","error")
            return render_template("register_role.html", role=role, role_label=labels[role])

        con=get_db()
        try:
            # Give a clean error instead of relying only on SQLite's UNIQUE exception.
            if con.execute("SELECT 1 FROM users WHERE lower(username)=lower(?) OR lower(email)=lower(?)",(username,email)).fetchone():
                flash("Username or email already exists. Please use a different one.","error")
                con.close()
                return render_template("register_role.html", role=role, role_label=labels[role])

            if role == "admin":
                existing=con.execute("SELECT 1 FROM institutions WHERE lower(code)=lower(?)",(institution_code,)).fetchone()
                if existing:
                    flash("Institute code already exists. Please choose a unique code.","error")
                    con.close()
                    return render_template("register_role.html", role=role, role_label=labels[role])
                cur=con.execute("INSERT INTO institutions(name,code,email) VALUES(%s,%s,%s) RETURNING id",(institution_name,institution_code,email))
                iid=cur.fetchone()["id"]
            else:
                inst=con.execute("SELECT * FROM institutions WHERE upper(code)=upper(?)",(institution_code,)).fetchone()
                if not inst:
                    flash("Invalid institute code. Ask your institute admin for the correct institute code.","error")
                    con.close()
                    return render_template("register_role.html", role=role, role_label=labels[role])
                iid=inst["id"]

            # Create the login account first, inside the same transaction.
            cur=con.execute(
                "INSERT INTO users(name,username,email,password,role,institution_id) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",
                (name,username,email,generate_password_hash(password),role,iid)
            )
            uid=cur.fetchone()["id"]

            import json
            student_item=None
            guardian_item=None
            trainer_item=None

            if role == "trainer":
                trainer_item={"id":next_id(TRAINERS),"name":name,"email":email,"phone":"","specialization":"","experience":0,"status":"Active","institution_id":iid}
                con.execute("INSERT INTO records(entity,id,payload) VALUES(?,?,?)",("trainers",trainer_item["id"],json.dumps(trainer_item)))

            elif role == "student":
                phone=request.form.get("phone","").strip()
                guardian_name=request.form.get("guardian_name","").strip()
                guardian_relation=request.form.get("guardian_relation","").strip() or "Guardian"
                guardian_phone=request.form.get("guardian_phone","").strip()
                guardian_address=request.form.get("guardian_address","").strip()

                student_item={
                    "id":next_id(STUDENTS),"name":name,"email":email,"phone":phone,
                    "course_id":None,"course_ids":[],"batch_id":None,
                    "enrollment_date":datetime.now().strftime("%Y-%m-%d"),
                    "status":"Active","guardian_id":None,"institution_id":iid
                }

                if guardian_name:
                    gid=next_id(GUARDIANS)
                    guardian_item={"id":gid,"name":guardian_name,"relation":guardian_relation,"phone":guardian_phone,"student_id":student_item["id"],"address":guardian_address,"institution_id":iid}
                    student_item["guardian_id"]=gid
                    con.execute("INSERT INTO records(entity,id,payload) VALUES(?,?,?)",("guardians",gid,json.dumps(guardian_item)))

                con.execute("INSERT INTO records(entity,id,payload) VALUES(?,?,?)",("students",student_item["id"],json.dumps(student_item)))

            con.commit()

            # Refresh only the affected in-memory collections after the transaction succeeds.
            if role == "trainer":
                TRAINERS[:] = load_entity("trainers")
            elif role == "student":
                STUDENTS[:] = load_entity("students")
                GUARDIANS[:] = load_entity("guardians")

        except Exception as e:
            con.rollback()
            flash("Account could not be created because the username, email, or institute code already exists.","error")
            return render_template("register_role.html", role=role, role_label=labels[role])
        except Exception as e:
            con.rollback()
            print("Registration error:",repr(e))
            flash("Account could not be created. Please verify the details and try again.","error")
            return render_template("register_role.html", role=role, role_label=labels[role])
        finally:
            con.close()

        flash("Account created successfully. Please sign in.","success")
        return redirect(url_for("role_login",role=role))

    return render_template("register_role.html", role=role, role_label=labels[role])

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_password():
    if request.method=="POST": flash("If the account exists, password reset instructions would be sent.","success"); return redirect(url_for("forgot_password"))
    return render_template("forgot_password.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

# ---------------------------------------------------------------------------
# ROLE-SCOPED DATA HELPERS

def current_institution_id():
    return session.get("institution_id", 1)

def current_institution_name():
    """Return the institute name stored for the currently signed-in account."""
    iid = current_institution_id()
    try:
        con = get_db()
        row = con.execute("SELECT name FROM institutions WHERE id=?", (iid,)).fetchone()
        con.close()
        if row and row["name"]:
            return row["name"]
    except Exception:
        pass
    return "My Institute"

@app.context_processor
def inject_institution_name():
    return {"institution_name": current_institution_name()}

def institution_filter(items):
    iid=current_institution_id()
    return [x for x in items if x.get("institution_id", 1)==iid]

def ensure_institution_fields():
    iid=current_institution_id()
    for entity in ("courses","trainers","batches","students","guardians","attendance","sessions","assessments","announcements","payments","materials","recordings","forum_posts"):
        for item in DATA.get(entity, []):
            item.setdefault("institution_id", 1)

# ---------------------------------------------------------------------------
def current_trainer():
    email = session.get("user_email")
    trainer = next((t for t in TRAINERS if t.get("email") == email and t.get("institution_id",1)==current_institution_id()), None)
    # Demo/legacy accounts may use a generic login email. Fall back to the
    # first active trainer so the seeded trainer account is fully functional.
    if trainer is None and session.get("user_role") == "trainer":
        trainer = next((t for t in TRAINERS if t.get("status") == "Active"), None)
    return trainer

def trainer_scope():
    t = current_trainer()
    if not t:
        return {"courses": [], "batches": [], "students": [], "guardians": [], "attendance": [], "sessions": [], "assessments": [], "materials": [], "announcements": [], "recordings": []}
    tid = t["id"]
    batches = [b for b in institution_filter(BATCHES) if b.get("trainer_id") == tid]
    batch_ids = {b["id"] for b in batches}
    course_ids = {b["course_id"] for b in batches}
    students = [st for st in institution_filter(STUDENTS) if st.get("batch_id") in batch_ids]
    student_ids = {st["id"] for st in students}
    return {
        "trainers": [t],
        "courses": [c for c in institution_filter(COURSES) if c.get("id") in course_ids],
        "batches": batches,
        "students": students,
        "guardians": [g for g in institution_filter(GUARDIANS) if g.get("student_id") in student_ids],
        "attendance": [a for a in institution_filter(ATTENDANCE) if a.get("student_id") in student_ids],
        "sessions": [x for x in institution_filter(SESSIONS) if x.get("trainer_id") == tid or x.get("batch_id") in batch_ids],
        "assessments": [a for a in institution_filter(ASSESSMENTS) if a.get("batch_id") in batch_ids],
        "materials": [m for m in institution_filter(MATERIALS) if m.get("batch_id") in batch_ids or m.get("course_id") in course_ids],
        "announcements": [a for a in institution_filter(ANNOUNCEMENTS) if a.get("audience") in {"All", "Trainers"}],
        "recordings": [x for x in institution_filter(SESSIONS) if x.get("recording_url") and (x.get("trainer_id") == tid or x.get("batch_id") in batch_ids)],
    }

def current_student():
    sid = session.get("student_id")
    if sid is not None:
        student = next((x for x in STUDENTS if x.get("id") == sid and x.get("institution_id",1) == current_institution_id()), None)
        if student is not None:
            return student
    email = (session.get("user_email") or "").strip().lower()
    student = next((x for x in STUDENTS if str(x.get("email","")).strip().lower() == email and x.get("institution_id",1)==current_institution_id()), None)
    return student

# DASHBOARD
# ---------------------------------------------------------------------------

@app.route("/home")
@login_required
def home():
    if session.get("user_role") != "admin":
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("user_role")
    if role == "admin":
        scoped = {"courses": institution_filter(COURSES), "batches": institution_filter(BATCHES), "students": institution_filter(STUDENTS), "sessions": institution_filter(SESSIONS)}
        admin_students=institution_filter(STUDENTS); admin_courses=institution_filter(COURSES); admin_trainers=institution_filter(TRAINERS); admin_batches=institution_filter(BATCHES); admin_payments=institution_filter(PAYMENTS); admin_sessions=institution_filter(SESSIONS); total_students=len(admin_students); total_att=sum(attendance_percentage(s["id"]) for s in admin_students)
        stats={"total_courses":len(admin_courses),"active_courses":len([c for c in admin_courses if c["status"]=="Active"]),"total_trainers":len(admin_trainers),"active_trainers":len([t for t in admin_trainers if t["status"]=="Active"]),"total_batches":len(admin_batches),"ongoing_batches":len([b for b in admin_batches if b["status"]=="Ongoing"]),"total_students":total_students,"active_students":len([s for s in admin_students if s["status"]=="Active"]),"attendance_pct":round(total_att/total_students) if total_students else 0,"total_revenue":sum(p["amount"] for p in admin_payments if p["status"]=="Paid"),"upcoming_sessions_count":len([x for x in admin_sessions if x["status"]=="Scheduled"])}
    elif role == "trainer":
        scoped=trainer_scope()
        students=scoped["students"]; total_students=len(students); total_att=sum(attendance_percentage(s["id"]) for s in students)
        stats={"total_courses":len(scoped["courses"]),"active_courses":len([c for c in scoped["courses"] if c["status"]=="Active"]),"total_trainers":1,"active_trainers":1,"total_batches":len(scoped["batches"]),"ongoing_batches":len([b for b in scoped["batches"] if b["status"]=="Ongoing"]),"total_students":total_students,"active_students":len([s for s in students if s["status"]=="Active"]),"attendance_pct":round(total_att/total_students) if total_students else 0,"upcoming_sessions_count":len([x for x in scoped["sessions"] if x["status"]=="Scheduled"])}
    else:
        student=current_student(); sid=student["id"] if student else 0
        enrolled_ids=set(student_course_ids(student)) if student else set()
        my_batches={e.get("batch_id") for e in student_enrollments(student) if e.get("batch_id")} if student else set()
        scoped={"courses":[c for c in institution_filter(COURSES) if c.get("id") in enrolled_ids],
                "batches":[b for b in institution_filter(BATCHES) if b.get("id") in my_batches],
                "students":[student] if student else [],
                "sessions":[x for x in institution_filter(SESSIONS) if student and x.get("batch_id") in my_batches]}
        stats={"total_students":1 if student else 0,
               "attendance_pct":attendance_percentage(sid) if student else 0,
               "upcoming_sessions_count":len([x for x in scoped["sessions"] if x["status"]=="Scheduled"]),
               "total_courses":len(scoped["courses"]),
               "total_batches":len(scoped["batches"])}
    # Students who have not enrolled in any course should see courses offered
    # by their own institute as recommendations on the dashboard.
    recommended_courses = []
    if role == "student":
        recommended_courses = [
            c for c in institution_filter(COURSES)
            if c.get("status") == "Active" and c.get("id") not in enrolled_ids
        ]
    recent_announcements = sorted(institution_filter(ANNOUNCEMENTS) if role=="admin" else (trainer_scope()["announcements"] if role=="trainer" else [a for a in institution_filter(ANNOUNCEMENTS) if a.get("audience") in {"All","Students"}]), key=lambda a:a["date"], reverse=True)[:4]
    upcoming_sessions=[x for x in scoped["sessions"] if x["status"]=="Scheduled"][:5]
    return render_template("dashboard.html",stats=stats,upcoming_sessions=upcoming_sessions,
                           recent_announcements=recent_announcements,batches=scoped["batches"],
                           courses=scoped["courses"],recommended_courses=recommended_courses,
                           role_label={"admin":"Institute Admin","trainer":"Trainer","student":"Student"}.get(role, "User"))

# ---------------------------------------------------------------------------
# PAGE ROUTES (server-rendered tables)
# ---------------------------------------------------------------------------

@app.route("/courses")
@login_required
def courses_page():
    role = session.get("user_role")
    if role == "admin":
        courses = institution_filter(COURSES); student_view = False; available_courses=[]; batches=institution_filter(BATCHES); trainers=institution_filter(TRAINERS)
    elif role == "trainer":
        courses = trainer_scope()["courses"]; student_view = False; available_courses=[]; batches=trainer_scope()["batches"]; trainers=[current_trainer()] if current_trainer() else []
    else:
        student=current_student(); enrolled_ids=set(student_course_ids(student)) if student else set()
        courses=[c for c in institution_filter(COURSES) if c.get("id") in enrolled_ids]
        available_courses=[c for c in institution_filter(COURSES) if c.get("status")=="Active" and c.get("id") not in enrolled_ids]
        student_view=True; batches=institution_filter(BATCHES); enrollments=student_enrollments(student)
    if role != "student": enrollments=[]
    return render_template("course.html", courses=courses, available_courses=available_courses, batches=batches, trainers=trainers if role != "student" else [], student_view=student_view, enrollments=enrollments)


@app.route("/trainers")
@login_required
def trainers_page():
    trainers = institution_filter(TRAINERS) if session.get("user_role") == "admin" else ([current_trainer()] if current_trainer() else [])
    return render_template("trainers.html", trainers=trainers)


@app.route("/batches")
@login_required
def batches_page():
    if session.get("user_role") == "admin":
        return render_template("batches.html", batches=institution_filter(BATCHES), courses=institution_filter(COURSES), trainers=institution_filter(TRAINERS))
    scoped=trainer_scope(); return render_template("batches.html", batches=scoped["batches"], courses=scoped["courses"], trainers=[current_trainer()] if current_trainer() else [])


@app.route("/students")
@login_required
def students_page():
    if session.get("user_role") == "admin":
        return render_template("students.html", students=institution_filter(STUDENTS), courses=institution_filter(COURSES), batches=institution_filter(BATCHES), guardians=institution_filter(GUARDIANS))
    scoped=trainer_scope(); return render_template("students.html", students=scoped["students"], courses=scoped["courses"], batches=scoped["batches"], guardians=scoped["guardians"])


@app.route("/guardians")
@login_required
def guardians_page():
    if session.get("user_role") == "admin":
        return render_template("guardians.html", guardians=institution_filter(GUARDIANS), students=institution_filter(STUDENTS))
    scoped=trainer_scope(); return render_template("guardians.html", guardians=scoped["guardians"], students=scoped["students"])


@app.route("/attendance")
@login_required
def attendance_page():
    role=session.get("user_role")
    if role == "student":
        student=current_student()
        attendance=[a for a in ATTENDANCE if student and a.get("student_id")==student.get("id")]
        students=[student] if student else []
        batches=[b for b in BATCHES if student and b.get("id")==student.get("batch_id")]
        return render_template("attendance.html", attendance=attendance, students=students, batches=batches, student_view=True)
    if role == "trainer":
        scoped=trainer_scope(); return render_template("attendance.html", attendance=scoped["attendance"], students=scoped["students"], batches=scoped["batches"], student_view=False)
    return render_template("attendance.html", attendance=institution_filter(ATTENDANCE), students=institution_filter(STUDENTS), batches=institution_filter(BATCHES), student_view=False)


@app.route("/sessions")
@login_required
def sessions_page():
    role=session.get("user_role")
    if role == "admin":
        return render_template("sessions.html", sessions=institution_filter(SESSIONS), batches=institution_filter(BATCHES), trainers=institution_filter(TRAINERS), student_view=False, trainer_view=False)
    if role == "trainer":
        scoped=trainer_scope(); return render_template("sessions.html", sessions=scoped["sessions"], batches=scoped["batches"], trainers=[current_trainer()] if current_trainer() else [], student_view=False, trainer_view=True)
    student=current_student(); batch_id=student.get("batch_id") if student else None
    sessions=[x for x in institution_filter(SESSIONS) if x.get("batch_id")==batch_id]
    batches=[b for b in institution_filter(BATCHES) if b.get("id")==batch_id]
    trainers=[t for t in institution_filter(TRAINERS) if any(b.get("trainer_id")==t.get("id") for b in batches)]
    return render_template("sessions.html", sessions=sessions, batches=batches, trainers=trainers, student_view=True, trainer_view=False)


@app.route("/live-session/<int:session_id>")
@login_required
def live_session_page(session_id):
    if session.get("user_role") != "student":
        return redirect(url_for("sessions_page"))
    student = current_student()
    live_session = next((x for x in institution_filter(SESSIONS) if x.get("id") == session_id), None)
    if not student or not live_session or live_session.get("batch_id") != student.get("batch_id"):
        return "Session not available for your account", 403
    duration_minutes = parse_duration_minutes(live_session.get("duration"))
    return render_template("live_session.html", live_session=live_session, duration_minutes=duration_minutes, student=student)

@app.route("/api/live-session/<int:session_id>/join", methods=["POST"])
@login_required
def live_session_join(session_id):
    if session.get("user_role") != "student":
        return jsonify({"error":"Only students can join tracked live sessions"}), 403
    student = current_student()
    live_session = next((x for x in institution_filter(SESSIONS) if x.get("id") == session_id), None)
    if not student or not live_session or live_session.get("batch_id") != student.get("batch_id"):
        return jsonify({"error":"Session not available for your account"}), 403
    duration = parse_duration_minutes(live_session.get("duration"))
    key = live_attendance_key(student.get("id"), session_id)
    state = LIVE_ATTENDANCE.get(key)
    if not state:
        state = {"student_id":student.get("id"), "session_id":session_id, "batch_id":live_session.get("batch_id"), "duration_minutes":duration, "active_seconds":0, "last_heartbeat":time.time(), "connected":True}
        LIVE_ATTENDANCE[key] = state
    else:
        state["connected"] = True
        state["last_heartbeat"] = time.time()
    return jsonify({"ok":True,"meeting_link":live_session.get("meeting_link"),"duration_minutes":duration,"required_minutes":round(duration*0.75,1)})

@app.route("/api/live-session/<int:session_id>/heartbeat", methods=["POST"])
@login_required
def live_session_heartbeat(session_id):
    if session.get("user_role") != "student":
        return jsonify({"error":"Access denied"}), 403
    student = current_student()
    key = live_attendance_key(student.get("id"), session_id) if student else None
    state = LIVE_ATTENDANCE.get(key) if key else None
    if not state:
        return jsonify({"error":"Live attendance has not been started"}), 400
    now = time.time()
    active = bool(request.json.get("active", True)) if request.is_json else True
    if state.get("connected") and state.get("last_heartbeat"):
        state["active_seconds"] += max(0, min(now - state["last_heartbeat"], 30)) if active else 0
    state["connected"] = active
    state["last_heartbeat"] = now
    duration_seconds = max(60, state.get("duration_minutes",1)*60)
    required = duration_seconds*0.75
    eligible = state["active_seconds"] >= required
    if state["active_seconds"] >= duration_seconds:
        result = finalize_live_attendance(student.get("id"), session_id)
        return jsonify({"ok":True,"completed":True, **(result or {})})
    return jsonify({"ok":True,"completed":False,"eligible":eligible,"active_minutes":round(state["active_seconds"]/60,1),"required_minutes":round(required/60,1),"percent":round(min(100,state["active_seconds"]/duration_seconds*100),1)})

@app.route("/api/live-session/<int:session_id>/leave", methods=["POST"])
@login_required
def live_session_leave(session_id):
    if session.get("user_role") != "student":
        return jsonify({"error":"Access denied"}), 403
    student=current_student()
    if not student:
        return jsonify({"error":"Student not found"}), 404
    result=finalize_live_attendance(student.get("id"), session_id)
    return jsonify({"ok":True, **(result or {})})

@app.route("/assessments")
@login_required
def assessments_page():
    role=session.get("user_role")
    if role == "student":
        student=current_student()
        enrolled_ids=set(student_course_ids(student)) if student else set()
        assessments=[a for a in ASSESSMENTS if student and (
            a.get("batch_id")==student.get("batch_id") or a.get("course_id") in enrolled_ids)]
        courses=[c for c in institution_filter(COURSES) if c.get("id") in enrolled_ids]
        batches=[b for b in BATCHES if student and b.get("id")==student.get("batch_id")]
        return render_template("assessments.html", assessments=assessments, courses=courses, batches=batches, student_view=True)
    if role == "trainer":
        scoped=trainer_scope(); return render_template("assessments.html", assessments=scoped["assessments"], courses=scoped["courses"], batches=scoped["batches"], student_view=False)
    return render_template("assessments.html", assessments=institution_filter(ASSESSMENTS), courses=institution_filter(COURSES), batches=institution_filter(BATCHES), student_view=False)


@app.route("/announcements")
@login_required
def announcements_page():
    role=session.get("user_role")
    if role == "admin":
        data=(institution_filter(ANNOUNCEMENTS), institution_filter(MATERIALS), institution_filter(COURSES), institution_filter(BATCHES))
    elif role == "trainer":
        scoped=trainer_scope(); data=(scoped["announcements"], scoped["materials"], scoped["courses"], scoped["batches"])
    else:
        student=current_student()
        bid=student.get("batch_id") if student else None
        enrolled_ids=set(student_course_ids(student)) if student else set()
        data=([a for a in institution_filter(ANNOUNCEMENTS) if a.get("audience") in {"All","Students"}],
              [m for m in institution_filter(MATERIALS) if m.get("batch_id")==bid or m.get("course_id") in enrolled_ids],
              [c for c in institution_filter(COURSES) if c.get("id") in enrolled_ids],
              [b for b in institution_filter(BATCHES) if b.get("id")==bid])
    return render_template("announcements.html", announcements=data[0], materials=data[1], courses=data[2], batches=data[3])


@app.route("/payments")
@login_required
def payments_page():
    role=session.get("user_role")
    if role == "student":
        student=current_student()
        payments=[p for p in PAYMENTS if student and p.get("student_id")==student.get("id")]
        total_paid=sum(p["amount"] for p in payments if p["status"]=="Paid")
        total_pending=0
        total_failed=sum(p["amount"] for p in payments if p["status"]=="Failed")
        return render_template("payments.html", payments=payments, students=[student] if student else [], total_paid=total_paid, total_pending=total_pending, total_failed=total_failed, student_view=True)
    total_paid=sum(p["amount"] for p in PAYMENTS if p["status"]=="Paid")
    total_pending=0
    total_failed=sum(p["amount"] for p in PAYMENTS if p["status"]=="Failed")
    return render_template("payments.html", payments=institution_filter(PAYMENTS), students=institution_filter(STUDENTS), total_paid=total_paid, total_pending=total_pending, total_failed=total_failed, student_view=False)


@app.route("/reports")
@login_required
def reports_page():
    role=session.get("user_role")
    if role == "student":
        student=current_student()
        my_attendance=[a for a in ATTENDANCE if student and a.get("student_id")==student.get("id")]
        enrolled_ids=set(student_course_ids(student)) if student else set()
        my_assessments=[a for a in institution_filter(ASSESSMENTS) if student and (
            a.get("batch_id")==student.get("batch_id") or a.get("course_id") in enrolled_ids)]
        return render_template("reports.html", courses=[], trainers=[], batches=[], students=[student] if student else [], attendance=my_attendance, assessments=my_assessments, payments=[], assessment_marks=ASSESSMENT_MARKS, student_view=True)
    if role == "trainer":
        scoped=trainer_scope(); return render_template("reports.html", courses=scoped["courses"], trainers=[current_trainer()] if current_trainer() else [], batches=scoped["batches"], students=scoped["students"], attendance=scoped["attendance"], assessments=scoped["assessments"], payments=[], assessment_marks=([m for m in ASSESSMENT_MARKS if m.get("institution_id",1)==current_institution_id() and m.get("assessment_id") in {a["id"] for a in scoped["assessments"]}] if role == "trainer" else institution_filter(ASSESSMENT_MARKS)), student_view=False)
    return render_template("reports.html", courses=institution_filter(COURSES), trainers=institution_filter(TRAINERS), batches=institution_filter(BATCHES), students=institution_filter(STUDENTS), attendance=institution_filter(ATTENDANCE), assessments=institution_filter(ASSESSMENTS), payments=institution_filter(PAYMENTS), assessment_marks=institution_filter(ASSESSMENT_MARKS), student_view=False)

# ---------------------------------------------------------------------------
# ASSESSMENT MARKS / REPORTS
@app.route("/api/assessments/<int:assessment_id>/marks", methods=["POST"])
@login_required
def upload_assessment_marks(assessment_id):
    if session.get("user_role") not in {"admin","trainer"}: return jsonify({"error":"Access denied"}),403
    assessment=find_by_id(ASSESSMENTS,assessment_id)
    if not assessment: return jsonify({"error":"Assessment not found"}),404
    if session.get("user_role")=="trainer" and assessment_id not in {a["id"] for a in trainer_scope()["assessments"]}: return jsonify({"error":"Access denied"}),403
    f=request.files.get("file")
    if not f: return jsonify({"error":"Excel file is required"}),400
    try:
        from openpyxl import load_workbook
        wb=load_workbook(f, data_only=True); ws=wb.active
        headers=[str(c.value).strip().lower() if c.value is not None else "" for c in ws[1]]
        idx={h:i for i,h in enumerate(headers)}
        sid_i=idx.get("student_id",idx.get("id")); marks_i=idx.get("marks",idx.get("mark"))
        if sid_i is None or marks_i is None: return jsonify({"error":"Excel must contain student_id and marks columns"}),400
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row[sid_i] in (None,"") or row[marks_i] in (None,""): continue
            sid=int(row[sid_i]); student=find_by_id(STUDENTS,sid)
            if not student: continue
            existing=next((r for r in ASSESSMENT_MARKS if r["assessment_id"]==assessment_id and r["student_id"]==sid),None)
            rec={"id":existing["id"] if existing else next_id(ASSESSMENT_MARKS),"assessment_id":assessment_id,"student_id":sid,"marks":float(row[marks_i]),"institution_id":current_institution_id()}
            if existing: existing.update(rec)
            else: ASSESSMENT_MARKS.append(rec)
        save_entity("assessment_marks",ASSESSMENT_MARKS)
        return jsonify({"message":"Assessment marks uploaded successfully"}),200
    except Exception as e: return jsonify({"error":f"Invalid Excel file: {e}"}),400

@app.route("/reports/student.pdf")
@login_required
def student_report_pdf():
    if session.get("user_role")!="student": return redirect(url_for("reports_page"))
    student=current_student();
    if not student: return "Student not found",404
    attendance_rows=[[a.get("date",""),a.get("status","")] for a in institution_filter(ATTENDANCE) if a.get("student_id")==student["id"]]
    assessment_rows=[]
    for m in institution_filter(ASSESSMENT_MARKS):
        if m.get("student_id")==student["id"]:
            a=find_by_id(institution_filter(ASSESSMENTS),m["assessment_id"]); assessment_rows.append([a.get("title","") if a else "",course_name(a.get("course_id")) if a else "",m.get("marks",0),a.get("max_marks",0) if a else ""])
    return export_student_pdf(student["name"], attendance_rows, assessment_rows)

def export_student_pdf(student_name, attendance_rows, assessment_rows):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph,Spacer
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    out=io.BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4); styles=getSampleStyleSheet(); story=[Paragraph("Student Performance Report",styles["Title"]),Paragraph(student_name,styles["Heading2"]),Paragraph("Attendance",styles["Heading3"]) ]
    at=[['Date','Status']]+attendance_rows; t=Table(at,repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f2747')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey)])); story.append(t); story.append(Spacer(1,16)); story.append(Paragraph("Assessment Marks",styles["Heading3"]))
    ar=[['Assessment','Course','Marks','Max Marks']]+assessment_rows; t2=Table(ar,repeatRows=1); t2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f2747')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey)])); story.append(t2); doc.build(story); out.seek(0); return send_file(out,as_attachment=True,download_name='student_report.pdf',mimetype='application/pdf')

def export_pdf_file(title,headers,rows,student_name):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate,Table,TableStyle,Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    out=io.BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4); styles=getSampleStyleSheet(); story=[Paragraph(title,styles["Title"]),Paragraph(student_name,styles["Heading2"])]; data=[headers]+rows; table=Table(data,repeatRows=1); table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0f2747")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.5,colors.grey)])); story.append(table); doc.build(story); out.seek(0); return send_file(out,as_attachment=True,download_name="student_assessment_report.pdf",mimetype="application/pdf")

# ---------------------------------------------------------------------------
# GENERIC CRUD API  (used by all management pages via fetch())
# ---------------------------------------------------------------------------

INT_FIELDS = {
    "fee", "experience", "capacity", "enrolled", "course_id", "trainer_id", "batch_id",
    "student_id", "guardian_id", "max_marks", "amount",
}


def coerce_types(payload):
    clean = {}
    for k, v in payload.items():
        if k in INT_FIELDS and v not in (None, ""):
            try:
                clean[k] = int(v)
            except (ValueError, TypeError):
                clean[k] = v
        else:
            clean[k] = v
    return clean


@app.route("/api/data/<entity>", methods=["GET", "POST"])
@login_required
def api_collection(entity):
    role=session.get("user_role")
    trainer_entities={"courses","trainers","batches","students","guardians","attendance","sessions","assessments","announcements","materials","recordings","assessment_marks"}
    if role != "admin" and not (role=="trainer" and entity in trainer_entities): return jsonify({"error":"Access denied"}),403
    if entity not in DATA:
        return jsonify({"error": "Unknown entity"}), 404
    items = DATA[entity]
    visible_items = institution_filter(items)
    if role == "trainer":
        scoped=trainer_scope()
        if entity in scoped:
            items_view=scoped[entity]
        else:
            items_view=visible_items
    else:
        items_view=visible_items
    if request.method == "GET":
        return jsonify(items_view)

    payload = coerce_types(request.get_json(force=True, silent=True) or {})
    if role == "trainer":
        scoped=trainer_scope(); t=current_trainer()
        if entity == "trainers":
            return jsonify({"error":"Trainers are managed by the institute admin."}),403
        if entity == "courses":
            return jsonify({"error":"Courses are managed by the institute admin; trainers can view only their assigned courses."}),403
        if entity == "batches" and payload.get("trainer_id") not in {t["id"]}:
            return jsonify({"error":"You can only create batches assigned to you"}),403
        if entity == "sessions" and payload.get("trainer_id") not in {t["id"]}:
            return jsonify({"error":"You can only create sessions for your trainer account"}),403
        if entity == "assessments" and payload.get("batch_id") not in {b["id"] for b in scoped["batches"]}:
            return jsonify({"error":"You can only create assessments for your batches"}),403
        if entity in {"students", "batches", "guardians"}:
            return jsonify({"error":"This section is managed by the institute admin."}),403
        if entity == "guardians" and payload.get("student_id") not in {st["id"] for st in scoped["students"]}:
            return jsonify({"error":"You can only manage guardians for your assigned students"}),403
        if entity == "attendance" and payload.get("student_id") not in {st["id"] for st in scoped["students"]}:
            return jsonify({"error":"You can only manage attendance for your assigned students"}),403
        if entity == "materials":
            allowed_batches={b["id"] for b in scoped["batches"]}
            allowed_courses={c["id"] for c in scoped["courses"]}
            if payload.get("batch_id") not in allowed_batches and payload.get("course_id") not in allowed_courses:
                return jsonify({"error":"You can only add materials to your assigned courses/batches"}),403
    payload["institution_id"] = current_institution_id()
    if entity == "payments" and payload.get("status") == "Pending":
        payload["status"] = "Failed"
    if entity == "batches":
        # New batches always start with zero enrolled students; enrollment increments this count.
        payload["enrolled"] = 0
        course = next((c for c in institution_filter(COURSES) if c.get("id") == payload.get("course_id")), None)
        trainer = next((t for t in institution_filter(TRAINERS) if t.get("id") == payload.get("trainer_id")), None)
        if not course:
            return jsonify({"error":"Select a valid course for this batch."}),400
        if not trainer:
            return jsonify({"error":"Select a valid trainer for this batch."}),400
        if int(payload.get("capacity") or 0) < 1:
            return jsonify({"error":"Batch capacity must be at least 1."}),400
    payload["id"] = next_id(items)
    embedded_batch = None
    if entity == "courses" and role == "admin":
        embedded_batch = {
            "name": payload.pop("batch_name", "").strip(),
            "trainer_id": payload.pop("batch_trainer_id", None),
            "start_date": payload.pop("batch_start_date", ""),
            "end_date": payload.pop("batch_end_date", ""),
            "timing": payload.pop("batch_timing", ""),
            "capacity": payload.pop("batch_capacity", 0),
            "status": payload.pop("batch_status", "Upcoming") or "Upcoming",
        }
        if embedded_batch["name"]:
            embedded_batch.update({"id": next_id(BATCHES), "course_id": payload["id"], "enrolled": 0, "institution_id": current_institution_id()})
            BATCHES.append(embedded_batch)
            save_entity("batches", BATCHES)
    if entity == "students":
        # Guardian details are captured from the student record and mirrored into the guardian table.
        gid = payload.get("guardian_id")
        guardian_fields = {k: payload.get(k, "") for k in ("guardian_name","guardian_relation","guardian_phone","guardian_address")}
        if guardian_fields["guardian_name"]:
            guardian = next((g for g in GUARDIANS if g.get("student_id")==payload["id"]), None)
            if guardian:
                guardian.update({"name":guardian_fields["guardian_name"],"relation":guardian_fields["guardian_relation"] or "Guardian","phone":guardian_fields["guardian_phone"],"address":guardian_fields["guardian_address"]})
            else:
                gid=next_id(GUARDIANS); guardian={"id":gid,"name":guardian_fields["guardian_name"],"relation":guardian_fields["guardian_relation"] or "Guardian","phone":guardian_fields["guardian_phone"],"student_id":payload["id"],"address":guardian_fields["guardian_address"],"institution_id":current_institution_id()}; GUARDIANS.append(guardian)
            payload["guardian_id"]=gid; save_entity("guardians",GUARDIANS)
        for k in guardian_fields: payload.pop(k,None)
    if entity == "sessions" and not payload.get("meeting_link"):
        payload["meeting_link"] = "https://meet.jit.si/" + re.sub(r"[^A-Za-z0-9]+", "-", current_institution_name()).strip("-") + "-" + secrets.token_urlsafe(7)
    items.append(payload); save_entity(entity, items)
    return jsonify({"message": "Created successfully", "item": payload}), 201


@app.route("/api/data/<entity>/<int:item_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_item(entity, item_id):
    role=session.get("user_role")
    trainer_entities={"courses","trainers","batches","students","guardians","attendance","sessions","assessments","announcements","materials","recordings","assessment_marks"}
    if role != "admin" and not (role=="trainer" and entity in trainer_entities): return jsonify({"error":"Access denied"}),403
    if entity not in DATA:
        return jsonify({"error": "Unknown entity"}), 404
    items = DATA[entity]
    item = next((x for x in institution_filter(items) if x.get("id")==item_id), None)
    if not item:
        return jsonify({"error": "Not found"}), 404
    if role == "trainer":
        if entity in {"trainers", "courses"}:
            return jsonify({"error":"Access denied"}),403
        scoped=trainer_scope()
        if item_id not in {x.get("id") for x in scoped.get(entity, [])}:
            return jsonify({"error":"Access denied"}),403

    if request.method == "GET":
        return jsonify(item)

    if request.method == "PUT":
        payload = coerce_types(request.get_json(force=True, silent=True) or {})
        payload.pop("id", None)
        if entity == "payments" and payload.get("status") == "Pending": payload["status"] = "Failed"
        if entity == "students":
            guardian_fields={k:payload.pop(k,"") for k in ("guardian_name","guardian_relation","guardian_phone","guardian_address")}
            if guardian_fields["guardian_name"]:
                guardian=next((g for g in GUARDIANS if g.get("student_id")==item.get("id")),None)
                if guardian:
                    guardian.update({"name":guardian_fields["guardian_name"],"relation":guardian_fields["guardian_relation"] or "Guardian","phone":guardian_fields["guardian_phone"],"address":guardian_fields["guardian_address"]})
                else:
                    gid=next_id(GUARDIANS); guardian={"id":gid,"name":guardian_fields["guardian_name"],"relation":guardian_fields["guardian_relation"] or "Guardian","phone":guardian_fields["guardian_phone"],"student_id":item.get("id"),"address":guardian_fields["guardian_address"],"institution_id":current_institution_id()}; GUARDIANS.append(guardian); item["guardian_id"]=gid
                save_entity("guardians",GUARDIANS)
        if entity == "courses" and role == "admin":
            batch_name=payload.pop("batch_name", None)
            batch_fields={"trainer_id":payload.pop("batch_trainer_id", None),"start_date":payload.pop("batch_start_date", None),"end_date":payload.pop("batch_end_date", None),"timing":payload.pop("batch_timing", None),"capacity":payload.pop("batch_capacity", None),"status":payload.pop("batch_status", None)}
            batch=next((b for b in BATCHES if b.get("course_id")==item.get("id") and b.get("institution_id")==current_institution_id()),None)
            if batch_name is not None and batch_name.strip():
                if batch:
                    batch["name"]=batch_name.strip()
                    for k,v in batch_fields.items():
                        if v not in (None, ""): batch[k]=v
                else:
                    batch={"id":next_id(BATCHES),"name":batch_name.strip(),"course_id":item.get("id"),"trainer_id":batch_fields["trainer_id"],"start_date":batch_fields["start_date"] or "","end_date":batch_fields["end_date"] or "","timing":batch_fields["timing"] or "","capacity":batch_fields["capacity"] or 0,"enrolled":0,"status":batch_fields["status"] or "Upcoming","institution_id":current_institution_id()}; BATCHES.append(batch)
                save_entity("batches",BATCHES)
        item.update(payload); save_entity(entity, items)
        return jsonify({"message": "Updated successfully", "item": item})

    if request.method == "DELETE":
        items.remove(item); save_entity(entity, items)
        return jsonify({"message": "Deleted successfully"})


@app.route("/api/enroll", methods=["POST"])
@login_required
def enroll_course():
    if session.get("user_role") != "student":
        return jsonify({"error":"Student access only"}),403
    student=current_student()
    if not student:
        return jsonify({"error":"Student record not found for this login. Please sign out and sign in again."}),404
    data=request.get_json(silent=True) or {}
    try:
        course_id=int(data.get("course_id"))
        batch_id=int(data.get("batch_id"))
    except (TypeError,ValueError):
        return jsonify({"error":"Course and batch are required."}),400
    payment_status=str(data.get("payment_status","Paid")).strip().title()
    if payment_status not in {"Paid","Failed"}:
        return jsonify({"error":"Invalid payment status."}),400

    iid=current_institution_id()
    course=next((c for c in COURSES if c.get("id")==course_id and c.get("institution_id",1)==iid and c.get("status")=="Active"),None)
    batch=next((b for b in BATCHES if b.get("id")==batch_id and b.get("institution_id",1)==iid and b.get("course_id")==course_id),None)
    if not course or not batch:
        return jsonify({"error":"Select a valid active course and batch."}),400
    capacity=int(batch.get("capacity") or 0)
    enrolled=int(batch.get("enrolled") or 0)
    if capacity < 1 or enrolled >= capacity:
        return jsonify({"error":"This batch is full. Please select another batch."}),400
    if course_id in student_course_ids(student):
        return jsonify({"error":"You are already enrolled in this course."}),400
    if payment_status == "Paid" and not str(course.get("payment_link") or "").strip():
        return jsonify({"error":"This course does not have a payment link yet. Please contact the institute admin."}),400
    if payment_status == "Failed":
        return jsonify({"error":"Payment failed. The course was not enrolled.","payment_failed":True}),400

    now=datetime.now().strftime("%Y-%m-%d")
    pid=next_id(PAYMENTS)
    payment={"id":pid,"student_id":student["id"],"course_id":course_id,"batch_id":batch_id,"amount":course.get("fee",0),"date":now,"method":"Online","status":"Paid","invoice_no":f"INV-{1000+pid}","institution_id":iid}
    PAYMENTS.append(payment)

    ids=student_course_ids(student)
    ids.append(course_id)
    student["course_ids"]=list(dict.fromkeys(ids))
    enrollments=student_enrollments(student)
    enrollments=[e for e in enrollments if e.get("course_id") != course_id]
    enrollments.append({"course_id":course_id,"batch_id":batch_id,"enrollment_date":now,"status":"Active"})
    student["enrollments"]=enrollments
    if not student.get("course_id"):
        student["course_id"]=course_id
    if not student.get("batch_id"):
        student["batch_id"]=batch_id
    student["enrollment_date"]=now
    student["status"]="Active"
    batch["enrolled"]=enrolled+1

    try:
        save_entity("payments",PAYMENTS)
        save_entity("students",STUDENTS)
        save_entity("batches",BATCHES)
        save_enrollment_record(iid, student["id"], course_id, batch_id, "Active", datetime.now())
    except Exception as exc:
        app.logger.exception("Enrollment save failed")
        # Restore in-memory state when persistence fails.
        if PAYMENTS and PAYMENTS[-1].get("id")==pid:
            PAYMENTS.pop()
        student["course_ids"]=ids[:-1] if ids and ids[-1]==course_id else ids
        student["enrollments"]=student_enrollments(student)[:-1]
        batch["enrolled"]=enrolled
        return jsonify({"error":"Enrollment could not be saved. Please try again."}),500
    return jsonify({"message":"Payment successful and course enrolled successfully.","course":course["name"],"batch":batch["name"]}),200

@app.route("/discussion-forum", methods=["GET","POST"])
@login_required
def discussion_forum():
    if request.method == "POST":
        title=request.form.get("title","").strip(); message=request.form.get("message","").strip()
        if title and message:
            FORUM_POSTS.insert(0,{"id":next_id(FORUM_POSTS),"title":title,"message":message,"author":session.get("user_name","User"),"role":session.get("user_role","student"),"date":datetime.now().strftime("%Y-%m-%d %H:%M")})
            save_entity("forum_posts",FORUM_POSTS)
            flash("Discussion posted successfully.","success")
        else:
            flash("Title and message are required.","error")
        return redirect(url_for("discussion_forum"))
    return render_template("discussion_forum.html", posts=FORUM_POSTS)

# ---------------------------------------------------------------------------
# LIVE RECORDINGS
# ---------------------------------------------------------------------------
@app.route("/api/session/<int:item_id>/generate-link", methods=["POST"])
@login_required
def generate_session_link(item_id):
    if session.get("user_role") not in {"admin","trainer"}: return jsonify({"error":"Access denied"}),403
    item=next((x for x in institution_filter(SESSIONS) if x.get("id")==item_id),None)
    if not item: return jsonify({"error":"Not found"}),404
    if session.get("user_role") == "trainer" and item.get("trainer_id") != current_trainer().get("id"):
        return jsonify({"error":"Access denied"}),403
    item["meeting_link"]="https://meet.jit.si/MyInstitute-"+secrets.token_urlsafe(7)
    save_entity("sessions",SESSIONS)
    return jsonify({"link":item["meeting_link"]})

@app.route("/api/session/<int:item_id>/recording", methods=["POST"])
@login_required
def add_session_recording(item_id):
    if session.get("user_role") not in {"admin","trainer"}: return jsonify({"error":"Access denied"}),403
    item=next((x for x in institution_filter(SESSIONS) if x.get("id")==item_id),None)
    if not item: return jsonify({"error":"Not found"}),404
    if session.get("user_role") == "trainer" and item.get("trainer_id") != current_trainer().get("id"):
        return jsonify({"error":"Access denied"}),403
    item["recording_url"]=request.form.get("recording_url","").strip()
    item["status"]="Completed"
    save_entity("sessions",SESSIONS)
    return jsonify({"ok":True})

@app.route("/recordings")
@login_required
def recordings_page():
    role=session.get("user_role")
    if role == "admin":
        recordings=[s for s in institution_filter(SESSIONS) if s.get("recording_url")]
    elif role == "trainer":
        recordings=trainer_scope()["recordings"]
    else:
        student=current_student(); bid=student.get("batch_id") if student else None
        recordings=[s for s in institution_filter(SESSIONS) if s.get("recording_url") and s.get("batch_id")==bid]
    return render_template("recordings.html", recordings=recordings)

# ---------------------------------------------------------------------------
# REPORT EXPORT  (PDF via reportlab, Excel via openpyxl)
# ---------------------------------------------------------------------------

REPORT_CONFIG = {
    "students": {
        "title": "Student Report",
        "headers": ["ID", "Name", "Email", "Phone", "Course", "Batch", "Status"],
        "rows": lambda: [[s["id"], s["name"], s["email"], s["phone"], course_name(s["course_id"]),
                           batch_name(s["batch_id"]), s["status"]] for s in institution_filter(STUDENTS)],
    },
    "courses": {
        "title": "Course Report",
        "headers": ["ID", "Name", "Code", "Category", "Duration", "Fee (INR)", "Status"],
        "rows": lambda: [[c["id"], c["name"], c["code"], c["category"], c["duration"], c["fee"], c["status"]]
                          for c in institution_filter(COURSES)],
    },
    "trainers": {
        "title": "Trainer Report",
        "headers": ["ID", "Name", "Email", "Phone", "Specialization", "Experience (Yrs)", "Status"],
        "rows": lambda: [[t["id"], t["name"], t["email"], t["phone"], t["specialization"], t["experience"], t["status"]]
                          for t in institution_filter(TRAINERS)],
    },
    "batches": {
        "title": "Batch Report",
        "headers": ["ID", "Name", "Course", "Trainer", "Start Date", "End Date", "Status", "Enrolled/Capacity"],
        "rows": lambda: [[b["id"], b["name"], course_name(b["course_id"]), trainer_name(b["trainer_id"]),
                           b["start_date"], b["end_date"], b["status"], str(b["enrolled"]) + "/" + str(b["capacity"])]
                          for b in institution_filter(BATCHES)],
    },
    "attendance": {
        "title": "Attendance Report",
        "headers": ["ID", "Student", "Batch", "Date", "Status"],
        "rows": lambda: [[a["id"], student_name(a["student_id"]), batch_name(a["batch_id"]), a["date"], a["status"]]
                          for a in institution_filter(ATTENDANCE)],
    },
    "assessments": {
        "title": "Assessment Report",
        "headers": ["ID", "Title", "Type", "Course", "Batch", "Date", "Max Marks", "Status"],
        "rows": lambda: [[a["id"], a["title"], a["type"], course_name(a["course_id"]), batch_name(a["batch_id"]),
                           a["date"], a["max_marks"], a["status"]] for a in institution_filter(ASSESSMENTS)],
    },
    "assessment_marks": {
        "title": "Assessment Marks Report",
        "headers": ["Assessment", "Student", "Course", "Marks", "Max Marks"],
        "rows": lambda: [[assessment_by_id(m["assessment_id"])["title"] if assessment_by_id(m["assessment_id"]) else "", student_name(m["student_id"]), course_name(assessment_by_id(m["assessment_id"])["course_id"]) if assessment_by_id(m["assessment_id"]) else "", m["marks"], assessment_by_id(m["assessment_id"])["max_marks"] if assessment_by_id(m["assessment_id"]) else ""] for m in institution_filter(ASSESSMENT_MARKS)],
    },
    "payments": {
        "title": "Payment Report",
        "headers": ["ID", "Invoice No", "Student", "Amount (INR)", "Date", "Method", "Status"],
        "rows": lambda: [[p["id"], p["invoice_no"], student_name(p["student_id"]), p["amount"], p["date"],
                           p["method"], p["status"]] for p in institution_filter(PAYMENTS)],
    },
}


@app.route("/reports/export/<report_type>/<fmt>")
@login_required
def export_report(report_type, fmt):
    """Export a report for the logged-in user's permitted scope."""
    fmt = (fmt or "").strip().lower()
    report_type = (report_type or "").strip().lower()

    if fmt not in {"pdf", "excel"}:
        flash("Invalid report format.", "error")
        return redirect(url_for("reports_page"))

    role = session.get("user_role")
    student = current_student() if role == "student" else None

    try:
        if role == "student":
            if not student:
                flash("Student record not found.", "error")
                return redirect(url_for("reports_page"))

            sid = student["id"]
            enrolled_ids = set(student_course_ids(student))
            if report_type == "attendance":
                headers = ["ID", "Student", "Batch", "Date", "Status"]
                rows = [[a.get("id"), student_name(sid), batch_name(a.get("batch_id")), a.get("date", ""), a.get("status", "")]
                        for a in institution_filter(ATTENDANCE) if a.get("student_id") == sid]
                title = "My Attendance Report"
            elif report_type == "assessments":
                headers = ["ID", "Title", "Type", "Course", "Batch", "Date", "Max Marks", "Status"]
                rows = [[a.get("id"), a.get("title", ""), a.get("type", ""), course_name(a.get("course_id")),
                         batch_name(a.get("batch_id")), a.get("date", ""), a.get("max_marks", ""), a.get("status", "")]
                        for a in institution_filter(ASSESSMENTS)
                        if a.get("batch_id") == student.get("batch_id") or a.get("course_id") in enrolled_ids]
                title = "My Assessment Report"
            elif report_type == "payments":
                headers = ["ID", "Invoice No", "Student", "Amount (INR)", "Date", "Method", "Status"]
                rows = [[p.get("id"), p.get("invoice_no", ""), student_name(sid), p.get("amount", 0),
                         p.get("date", ""), p.get("method", ""), p.get("status", "")]
                        for p in institution_filter(PAYMENTS) if p.get("student_id") == sid]
                title = "My Payment Report"
            else:
                flash("This report is not available for student accounts.", "error")
                return redirect(url_for("reports_page"))
        else:
            config = REPORT_CONFIG.get(report_type)
            if not config:
                flash("Unknown report type requested.", "error")
                return redirect(url_for("reports_page"))
            headers = config["headers"]
            rows = config["rows"]()
            title = config["title"]

        if fmt == "excel":
            return export_excel(title, headers, rows)
        return export_pdf(title, headers, rows)
    except Exception as exc:
        app.logger.exception("Report export failed")
        flash(f"Report download failed: {exc}", "error")
        return redirect(url_for("reports_page"))

def export_excel(title, headers, rows):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(size=14, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor="0B1F44")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    ws.cell(row=2, column=1, value="Generated: " + datetime.now().strftime("%d-%b-%Y %H:%M"))
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))

    header_row = 4
    for idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=idx, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1E40AF")
        cell.alignment = Alignment(horizontal="center")

    for r, row in enumerate(rows, start=header_row + 1):
        for c, val in enumerate(row, start=1):
            ws.cell(row=r, column=c, value=val)

    for idx, h in enumerate(headers, start=1):
        max_len = max([len(str(h))] + [len(str(row[idx - 1])) for row in rows]) if rows else len(str(h))
        ws.column_dimensions[get_column_letter(idx)].width = max(12, min(max_len + 4, 40))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = title.lower().replace(" ", "_") + "_" + datetime.now().strftime("%Y%m%d") + ".xlsx"
    return send_file(buf, as_attachment=True, download_name=filename,
                      mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def export_pdf(title, headers, rows):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4),
                             topMargin=1.5 * cm, bottomMargin=1.5 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleNavy", parent=styles["Title"], textColor=colors.HexColor("#0B1F44"))
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], textColor=colors.HexColor("#64748B"), fontSize=9)

    elements = [
        Paragraph("My Institute LMS &mdash; " + title, title_style),
        Paragraph("Generated: " + datetime.now().strftime("%d-%b-%Y %H:%M"), sub_style),
        Spacer(1, 14),
    ]

    table_data = [headers] + [[str(v) for v in row] for row in rows]
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    filename = title.lower().replace(" ", "_") + "_" + datetime.now().strftime("%Y%m%d") + ".pdf"
    return send_file(buf, as_attachment=True, download_name=filename, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
