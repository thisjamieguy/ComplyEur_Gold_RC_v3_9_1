# ComplyEur Product Specification

## Product Overview

**ComplyEur** is a secure, local-only web application that helps UK companies track employee travel days within the Schengen Area to ensure compliance with the EU 90/180-day rule. The application is built with privacy-first principles and GDPR compliance at its core.

## Purpose

Track employee travel to EU/Schengen countries and automatically calculate compliance with the 90/180-day rule:
- Employees can spend a maximum of 90 days within any 180-day rolling window in the Schengen Area
- The system calculates real-time compliance status and remaining days
- Prevents legal violations by alerting when limits are approaching or exceeded

## Core Features

### 1. Employee Management
- Add and manage employee records (name only - minimal data collection)
- View employee-specific travel history and compliance status

### 2. Trip Tracking
- Record EU/Schengen trips with entry/exit dates and country
- Support for ongoing trips (missing exit dates)
- Automatic calculation of travel days within rolling 180-day windows

### 3. Compliance Monitoring
- Real-time calculation of days used and remaining in current 180-day window
- Color-coded risk assessment:
  - **Green**: Safe (≥30 days remaining)
  - **Orange/Amber**: Caution (10-29 days remaining)
  - **Red**: High risk (<10 days remaining or exceeded)
- Earliest next safe entry date calculation

### 4. Calendar View
- Visual six-month calendar showing trip history
- Interactive drag-and-drop trip management
- Mobile touch support
- Trip reassignment between employees with conflict validation

### 5. Data Export & Reporting
- Export trip data to CSV
- Generate PDF compliance reports
- GDPR-compliant data export for DSAR (Data Subject Access Requests)

### 6. Security & Privacy
- Local-only storage (no cloud, no third parties)
- Secure authentication with password hashing (Argon2)
- Session management with idle timeout
- Audit logging for all actions
- GDPR-compliant data retention and anonymization

### 7. EU Travel News
- Real-time news feed filtered for EU/Schengen travel advisories
- Policy updates (ETIAS, EES, Schengen changes)
- Country-specific travel advice

## Technical Architecture

### Backend
- **Framework**: Python Flask
- **Database**: SQLite (local file storage)
- **Authentication**: Session-based with cookies
- **Security**: CSRF protection, rate limiting, secure headers

### Frontend
- **UI**: HTML, CSS, JavaScript (vanilla JS, no frameworks)
- **Design**: Minimal, clean interface (Apple-style minimalism)
- **Responsive**: Mobile-friendly with touch support

### Testing
- Playwright for end-to-end testing
- Automated test suites for calendar functionality
- Excel import validation tests

## User Workflows

### Admin User Flow
1. **Login**: Authenticate with username/password
2. **Dashboard**: View all employees with compliance status at a glance
3. **Add Employee**: Create new employee record (name only)
4. **Add Trip**: Record travel entry/exit dates and country
5. **Calendar View**: Visualise trips on interactive calendar
6. **Export**: Generate CSV or PDF reports
7. **Settings**: Configure data retention, session timeout, risk thresholds

### Key Interactions
- **Trip Entry**: Form-based entry with date pickers and country dropdown
- **Calendar Interaction**: Drag trips to move dates, resize trips, reassign between employees
- **Compliance Checks**: Real-time validation prevents overlapping trips and invalid dates
- **Risk Alerts**: Visual indicators (colors, progress bars) show compliance status

## Data Model

### Minimal Data Collection (GDPR-Compliant)
- **Employee**: Name only (no email, phone, address)
- **Trip**: Country code, entry date, exit date, optional purpose
- **No tracking**: No analytics, cookies (beyond functional session cookies), or third-party services

### Database Schema
- **Employees**: id, name, created_at
- **Trips**: id, employee_id, country, entry_date, exit_date, purpose, created_at
- **Admin**: Authentication and session management

## Compliance Requirements

### GDPR Compliance
- Data minimisation (only essential fields)
- Local-only storage (no cloud)
- Data retention policies
- DSAR tools for data subject access requests
- No tracking or analytics

### EU 90/180 Rule Compliance
- Accurate rolling 180-day window calculation
- Real-time compliance status
- Early warning system for approaching limits
- Validation to prevent overlapping trips

## Security Features

- Password hashing (Argon2)
- Session security (HTTPOnly, SameSite=Strict cookies)
- CSRF protection
- Rate limiting on login attempts
- Security headers (XSS protection, content type options)
- Audit logging for compliance tracking

## Performance Requirements

- Fast page loads (<2 seconds)
- Real-time compliance calculations
- Responsive calendar rendering
- Efficient database queries with indexing

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- Touch support for calendar interactions

## Deployment

- **Local**: Run via `python run_local.py` (development)
- **Production**: Deploy to Render or IONOS with HTTPS
- **Database**: SQLite file (local storage)
- **No external dependencies**: Self-contained application

## Future Enhancements (Planned)

- Role-based access control (admin/employee roles)
- Multi-company support
- API endpoints for integration
- Advanced reporting and analytics

