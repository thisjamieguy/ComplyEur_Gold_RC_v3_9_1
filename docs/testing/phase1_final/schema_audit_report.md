# Schema Audit Report
Generated: 2025-11-12T14:06:52.598106

## Database Information
- **Path**: /Users/jameswalsh/Desktop/Dev/Web Projects/ComplyEur/ComplyEur v1.0.0 Post MVP/data/eu_tracker.db
- **WAL Mode**: WAL (Enabled)
- **Integrity Check**: PASS
- **Integrity Details**: ok

## Tables

### admin

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| password_hash | TEXT | True |  | False |
| company_name | TEXT | False |  | False |
| full_name | TEXT | False |  | False |
| email | TEXT | False |  | False |
| phone | TEXT | False |  | False |


### alerts

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| employee_id | INTEGER | True |  | False |
| risk_level | TEXT | True |  | False |
| message | TEXT | True |  | False |
| created_at | TIMESTAMP | False | CURRENT_TIMESTAMP | False |
| resolved | INTEGER | False | 0 | False |
| email_sent | INTEGER | False | 0 | False |

#### Indexes

- idx_alerts_created_at
- idx_alerts_employee_active


### employees

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| name | TEXT | True |  | False |

#### Indexes

- idx_employees_name
- sqlite_autoindex_employees_1


### news_cache

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| source_id | INTEGER | False |  | False |
| title | TEXT | True |  | False |
| url | TEXT | False |  | False |
| published_at | DATETIME | False |  | False |
| summary | TEXT | False |  | False |
| fetched_at | DATETIME | False | CURRENT_TIMESTAMP | False |

#### Indexes

- idx_news_cache_fetched
- idx_news_cache_source
- sqlite_autoindex_news_cache_1


### news_sources

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| name | TEXT | True |  | False |
| url | TEXT | True |  | False |
| enabled | INTEGER | False | 1 | False |
| license_note | TEXT | False |  | False |


### sqlite_sequence

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| name |  | False |  | False |
| seq |  | False |  | False |


### trips

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | False |  | True |
| employee_id | INTEGER | True |  | False |
| country | TEXT | True |  | False |
| entry_date | TEXT | True |  | False |
| exit_date | TEXT | True |  | False |
| travel_days | INTEGER | False | 0 | False |
| created_at | TEXT | False | datetime('now') | False |
| validation_note | TEXT | False |  | False |
| is_private | BOOLEAN | False | 0 | False |
| job_ref | TEXT | False |  | False |
| ghosted | BOOLEAN | False | 0 | False |
| purpose | TEXT | False |  | False |

#### Indexes

- idx_trips_employee_dates
- idx_trips_dates
- idx_trips_entry_date
- idx_trips_employee_entry
- idx_trips_exit_date
- idx_trips_employee_id


### user

#### Columns

| Name | Type | Not Null | Default | Primary Key |
|------|------|----------|---------|-------------|
| id | INTEGER | True |  | True |
| username | VARCHAR(64) | True |  | False |
| password_hash | VARCHAR(256) | True |  | False |
| mfa_secret | VARCHAR(32) | False |  | False |
| role | VARCHAR(32) | True |  | False |
| oauth_provider | VARCHAR(32) | False |  | False |
| oauth_id | VARCHAR(128) | False |  | False |
| created_at | DATETIME | False |  | False |
| last_login_at | DATETIME | False |  | False |
| failed_attempts | INTEGER | False |  | False |
| locked_until | DATETIME | False |  | False |

#### Indexes

- ix_user_username


