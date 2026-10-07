"""Initialize the PostgreSQL schema for the LMS.

Usage:
    set DATABASE_URL=postgresql://postgres:password@localhost:5432/lms
    python migrate_to_postgres.py
"""
import os
from db_schema import init_schema

if not os.getenv("DATABASE_URL"):
    raise SystemExit("DATABASE_URL is required. Example: postgresql://postgres:password@localhost:5432/lms")

init_schema(os.environ["DATABASE_URL"])
print("PostgreSQL LMS schema created successfully.")
