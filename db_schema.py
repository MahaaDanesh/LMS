"""Standalone PostgreSQL schema initializer used before first app startup."""
from sqlalchemy import create_engine, text

def init_schema(url):
    engine=create_engine(url, pool_pre_ping=True)
    statements=[
        "CREATE TABLE IF NOT EXISTS institutions (id BIGSERIAL PRIMARY KEY, name VARCHAR(200) NOT NULL, code VARCHAR(80) UNIQUE NOT NULL, email VARCHAR(255), created_at TIMESTAMPTZ DEFAULT NOW())",
        "CREATE TABLE IF NOT EXISTS users (id BIGSERIAL PRIMARY KEY, name VARCHAR(200) NOT NULL, username VARCHAR(120) NOT NULL, email VARCHAR(255), password TEXT NOT NULL, role VARCHAR(30) NOT NULL, institution_id BIGINT NOT NULL REFERENCES institutions(id), created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(institution_id, username), UNIQUE(institution_id, email))",
        "CREATE TABLE IF NOT EXISTS records (entity VARCHAR(80) NOT NULL, id BIGINT NOT NULL, institution_id BIGINT NOT NULL REFERENCES institutions(id), payload JSONB NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW(), PRIMARY KEY(entity,id))",
        "CREATE TABLE IF NOT EXISTS enrollments (id BIGSERIAL PRIMARY KEY, institution_id BIGINT NOT NULL REFERENCES institutions(id), student_id BIGINT NOT NULL, course_id BIGINT NOT NULL, batch_id BIGINT NOT NULL, status VARCHAR(30) DEFAULT 'Active', enrolled_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(institution_id, student_id, course_id))",
        "CREATE TABLE IF NOT EXISTS attendance_records (id BIGSERIAL PRIMARY KEY, institution_id BIGINT NOT NULL REFERENCES institutions(id), student_id BIGINT NOT NULL, batch_id BIGINT, session_id BIGINT, attendance_date DATE, active_seconds INTEGER DEFAULT 0, required_seconds INTEGER DEFAULT 0, status VARCHAR(20), auto_tracked BOOLEAN DEFAULT FALSE, created_at TIMESTAMPTZ DEFAULT NOW(), UNIQUE(institution_id, student_id, session_id))",
        "CREATE INDEX IF NOT EXISTS ix_users_institution_role ON users(institution_id, role)",
        "CREATE INDEX IF NOT EXISTS ix_records_institution_entity ON records(institution_id, entity)",
        "CREATE INDEX IF NOT EXISTS ix_records_entity_updated ON records(entity, updated_at DESC)",
        "CREATE INDEX IF NOT EXISTS ix_enrollments_student ON enrollments(institution_id, student_id)",
        "CREATE INDEX IF NOT EXISTS ix_enrollments_batch ON enrollments(institution_id, batch_id)",
        "CREATE INDEX IF NOT EXISTS ix_attendance_student_date ON attendance_records(institution_id, student_id, attendance_date)",
        "CREATE INDEX IF NOT EXISTS ix_attendance_session ON attendance_records(institution_id, session_id, student_id)",
    ]
    with engine.begin() as conn:
        for sql in statements: conn.execute(text(sql))
    engine.dispose()
