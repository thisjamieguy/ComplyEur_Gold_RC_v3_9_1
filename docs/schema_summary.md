# ComplyEur Database Schema Summary

**Version**: 3.9.1 (Gold Release Candidate)  
**Last Updated**: 2025-11-12

This document provides a comprehensive overview of the ComplyEur database schema, including all tables, fields, relationships, and indexes.

---

## Database Overview

- **Database Engine**: SQLite 3
- **Database File**: `data/complyeur.db` (configurable via `DATABASE_PATH`)
- **Journal Mode**: WAL (Write-Ahead Logging)
- **Foreign Keys**: Enabled
- **Character Encoding**: UTF-8

---

## Tables

### 1. `employees`

**Purpose**: Store employee records for compliance tracking.

**Schema**:
```sql
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique employee identifier
- `name` (TEXT, NOT NULL): Employee full name (only personal data field)
- `created_at` (TIMESTAMP): Record creation timestamp

**Indexes**:
- `idx_employees_name`: Index on `name` with NOCASE collation for case-insensitive sorting

**Relationships**:
- One-to-many with `trips` (CASCADE delete)
- One-to-many with `alerts` (CASCADE delete)

**Notes**:
- Employee names are unique (enforced by application logic)
- Deleted automatically when no trips remain (retention policy)

---

### 2. `trips`

**Purpose**: Store EU/Schengen trip records for 90/180-day compliance calculations.

**Schema**:
```sql
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    country TEXT NOT NULL,
    entry_date DATE NOT NULL,
    exit_date DATE NOT NULL,
    purpose TEXT,
    job_ref TEXT,
    ghosted BOOLEAN DEFAULT 0,
    travel_days INTEGER DEFAULT 0,
    is_private BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique trip identifier
- `employee_id` (INTEGER, NOT NULL, FOREIGN KEY): Reference to `employees.id`
- `country` (TEXT, NOT NULL): 2-letter ISO country code (e.g., FR, DE, IT)
- `entry_date` (DATE, NOT NULL): Date of entry into country (YYYY-MM-DD)
- `exit_date` (DATE, NOT NULL): Date of exit from country (YYYY-MM-DD)
- `purpose` (TEXT): Optional trip purpose/description
- `job_ref` (TEXT): Optional job reference number
- `ghosted` (BOOLEAN, DEFAULT 0): Flag for "ghosted" trips (not counted in calculations)
- `travel_days` (INTEGER, DEFAULT 0): Cached trip duration (for performance)
- `is_private` (BOOLEAN, DEFAULT 0): Privacy flag (when true, country stored as 'XX')
- `created_at` (TIMESTAMP): Record creation timestamp

**Indexes**:
- `idx_trips_employee_id`: Index on `employee_id` for employee lookups
- `idx_trips_entry_date`: Index on `entry_date` for date range queries
- `idx_trips_exit_date`: Index on `exit_date` for date range queries
- `idx_trips_dates`: Composite index on `(entry_date, exit_date)`
- `idx_trips_employee_dates`: Composite index on `(employee_id, entry_date, exit_date)` for dashboard queries

**Relationships**:
- Many-to-one with `employees` (CASCADE delete)

**Constraints**:
- `entry_date` must be <= `exit_date` (enforced by application logic)
- `country` must be valid 2-letter ISO code (enforced by application logic)
- Trips cannot overlap for same employee (enforced by application logic)

**Notes**:
- Ireland (IE) trips are tracked but excluded from Schengen calculations
- Private trips (`is_private=1`) have country stored as 'XX' for privacy
- `travel_days` is cached for performance but can be recalculated

---

### 3. `alerts`

**Purpose**: Store compliance alerts and warnings for employees.

**Schema**:
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    risk_level TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved INTEGER DEFAULT 0,
    email_sent INTEGER DEFAULT 0,
    FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique alert identifier
- `employee_id` (INTEGER, NOT NULL, FOREIGN KEY): Reference to `employees.id`
- `risk_level` (TEXT, NOT NULL): Risk level ('green', 'amber', 'red')
- `message` (TEXT, NOT NULL): Alert message text
- `created_at` (TIMESTAMP): Alert creation timestamp
- `resolved` (INTEGER, DEFAULT 0): Resolution flag (0=unresolved, 1=resolved)
- `email_sent` (INTEGER, DEFAULT 0): Email notification flag (0=not sent, 1=sent)

**Indexes**:
- `idx_alerts_employee_active`: Composite index on `(employee_id, resolved)` for active alert queries
- `idx_alerts_created_at`: Index on `created_at` for chronological sorting

**Relationships**:
- Many-to-one with `employees` (CASCADE delete)

**Notes**:
- Alerts are automatically generated when compliance thresholds are exceeded
- Resolved alerts are retained for audit purposes

---

### 4. `admin`

**Purpose**: Store administrator account information.

**Schema**:
```sql
CREATE TABLE admin (
    id INTEGER PRIMARY KEY,
    password_hash TEXT NOT NULL,
    company_name TEXT,
    full_name TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Always 1 (single admin account)
- `password_hash` (TEXT, NOT NULL): Argon2/bcrypt hashed password (never plaintext)
- `company_name` (TEXT): Optional company name
- `full_name` (TEXT): Optional admin full name
- `email` (TEXT): Optional admin email
- `phone` (TEXT): Optional admin phone
- `created_at` (TIMESTAMP): Account creation timestamp

**Indexes**:
- None (single row table)

**Relationships**:
- None

**Notes**:
- Single admin account (id always 1)
- Password is hashed using Argon2 (primary) or bcrypt (fallback)
- Admin details are optional and not used for authentication

---

### 5. `news_sources`

**Purpose**: Store RSS feed sources for EU travel news.

**Schema**:
```sql
CREATE TABLE news_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    license_note TEXT
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique source identifier
- `name` (TEXT, NOT NULL): Source name (e.g., "France Travel Advice")
- `url` (TEXT, NOT NULL): RSS feed URL
- `enabled` (INTEGER, DEFAULT 1): Enable/disable flag (0=disabled, 1=enabled)
- `license_note` (TEXT): Optional license information

**Indexes**:
- None

**Relationships**:
- One-to-many with `news_cache`

**Notes**:
- Pre-seeded with EU Commission and GOV.UK travel advice feeds
- Sources can be enabled/disabled via admin settings

---

### 6. `news_cache`

**Purpose**: Cache fetched news articles for performance.

**Schema**:
```sql
CREATE TABLE news_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    published_at DATETIME,
    summary TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES news_sources (id)
)
```

**Fields**:
- `id` (INTEGER, PRIMARY KEY): Unique cache entry identifier
- `source_id` (INTEGER, FOREIGN KEY): Reference to `news_sources.id`
- `title` (TEXT, NOT NULL): Article title
- `url` (TEXT, UNIQUE): Article URL (unique constraint prevents duplicates)
- `published_at` (DATETIME): Article publication date
- `summary` (TEXT): Article summary/excerpt
- `fetched_at` (DATETIME): Cache entry creation timestamp

**Indexes**:
- `idx_news_cache_source`: Index on `source_id` for source lookups
- `idx_news_cache_fetched`: Index on `fetched_at` for cache expiration queries

**Relationships**:
- Many-to-one with `news_sources`

**Notes**:
- Cache entries are automatically expired after configurable period (default 7 days)
- Unique constraint on `url` prevents duplicate articles

---

## Database Relationships Diagram

```
employees (1) ──< (many) trips
employees (1) ──< (many) alerts
news_sources (1) ──< (many) news_cache
admin (standalone)
```

---

## Indexes Summary

### Performance Indexes

1. **`idx_trips_employee_id`**: Fast employee trip lookups
2. **`idx_trips_entry_date`**: Date range queries
3. **`idx_trips_exit_date`**: Date range queries
4. **`idx_trips_dates`**: Composite date queries
5. **`idx_trips_employee_dates`**: Dashboard queries (employee + dates)
6. **`idx_employees_name`**: Case-insensitive name sorting
7. **`idx_alerts_employee_active`**: Active alert queries
8. **`idx_alerts_created_at`**: Chronological alert sorting
9. **`idx_news_cache_source`**: News source lookups
10. **`idx_news_cache_fetched`**: Cache expiration queries

---

## Data Integrity

### Foreign Key Constraints

- `trips.employee_id` → `employees.id` (CASCADE delete)
- `alerts.employee_id` → `employees.id` (CASCADE delete)
- `news_cache.source_id` → `news_sources.id`

### Application-Level Constraints

- Employee names must be unique
- Trip entry_date <= exit_date
- Country codes must be valid 2-letter ISO codes
- Trips cannot overlap for same employee (unless allowed by admin)

---

## Database Maintenance

### Integrity Checks

Run integrity check:
```sql
PRAGMA integrity_check;
```

Expected result: `ok`

### WAL Mode

Database uses WAL (Write-Ahead Logging) mode for better concurrency:
```sql
PRAGMA journal_mode = WAL;
```

### Backup

Database backups are stored in:
- `data/backups/` - Encrypted backups (optional)
- Automatic backups on startup/shutdown (if configured)

---

## Migration Notes

### Schema Evolution

The schema supports backward compatibility through:
- `ALTER TABLE` statements with `IF NOT EXISTS` checks
- Graceful handling of missing columns
- Default values for new columns

### Version History

- **v3.9.1**: Current schema (Gold Release Candidate)
- **v1.6.4**: Added `is_private`, `job_ref`, `ghosted` columns
- **v1.5.0**: Added `travel_days` column
- **v1.0.0**: Initial schema

---

## Data Retention

### Automatic Retention

- **Trips**: Deleted after 36 months (configurable via `RETENTION_MONTHS`)
- **Employees**: Deleted when no trips remain
- **Alerts**: Retained indefinitely (for audit)
- **News Cache**: Expired after 7 days (configurable)

### Manual Deletion

- Admin can manually delete employees and trips
- All deletions are logged in audit trail
- CASCADE delete ensures referential integrity

---

## Performance Considerations

### Query Optimization

- Composite indexes for common query patterns
- NOCASE collation for case-insensitive sorting
- Cached `travel_days` field for performance

### Database Size

- Typical size: ~500 KB for 100 employees, 1000 trips
- Grows linearly with data volume
- WAL files are temporary and can be checkpointed

---

## Security Considerations

### Access Control

- Database file permissions control access
- No network exposure (local-only)
- Admin-only access via application

### Data Protection

- Passwords hashed (never plaintext)
- Private trips have country masked ('XX')
- Audit logging for all data modifications

---

## Additional Resources

- `app/models.py` - Schema definition and models
- `compliance/data_map.yaml` - GDPR data processing map
- `docs/security_audit.md` - Security audit report

---

**Schema Verified**: Database schema has been verified for integrity, performance, and security. All relationships and constraints are properly enforced.

