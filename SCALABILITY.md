# Scalability notes

- PostgreSQL is the persistent source of truth.
- Connection pooling prevents opening a new database connection for every request.
- Institution/entity indexes support multi-institute filtering.
- Enrollment and attendance are also written to normalized indexed PostgreSQL tables for high-volume queries and report generation.
- Existing report exports continue to use the same product routes, but their source data is PostgreSQL-backed.
- The current UI preserves the existing product behavior; pagination can be added to individual list endpoints without changing the database model.
