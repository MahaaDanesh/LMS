# My Institute LMS — PostgreSQL Scalable Version

This version keeps the existing Admin / Trainer / Student product functionality while moving persistent application data from SQLite/in-memory storage to PostgreSQL.

## PostgreSQL-backed functionality
- Admin, Trainer and Student account CRUD
- Institution isolation
- Course and batch CRUD
- Student/trainer/guardian CRUD
- Enrollment + payment persistence
- Attendance persistence, including 75% live-class tracking
- Assessments and assessment marks
- Sessions and recording links
- Announcements/materials
- Reports and exports

## Database architecture
PostgreSQL is the source of truth. The application uses a connection pool (`DB_POOL_MIN` / `DB_POOL_MAX`) and JSONB records for compatibility with the existing product screens, plus normalized high-volume tables for `enrollments` and `attendance_records` with indexes for reporting and filtering.

## Setup
1. Create a PostgreSQL database named `lms`.
2. Set `DATABASE_URL`:
   `postgresql://postgres:YOUR_PASSWORD@localhost:5432/lms`
3. Create the schema:
   `python migrate_to_postgres.py`
4. Install:
   `pip install -r requirements.txt`
5. Run:
   `python app.py`

The app creates/updates its required PostgreSQL tables automatically as well.

### Render / production
Set `DATABASE_URL` to your managed PostgreSQL connection string. Do not commit passwords or `.env` files.

## Demo accounts
- Admin: `admin` / `admin123`
- Trainer: `trainer` / `trainer123`
- Student: `student` / `student123`

Change these credentials before production deployment.
