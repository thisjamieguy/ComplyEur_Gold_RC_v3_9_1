# ComplyEur Changelog

All notable changes to the ComplyEur project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.9.1] - 2025-11-12 - Gold Release Candidate

### 🎯 Release Status
**Gold Release Candidate** - Production-ready stable build with comprehensive testing and documentation.

### ✨ Features
- **Core Compliance Logic**: Stable 90/180-day rule calculations with rolling window support
- **Employee Management**: Full CRUD operations for employee records
- **Trip Tracking**: Entry/exit date tracking with country validation
- **Calendar View**: Interactive calendar with drag-and-drop trip management
- **Risk Assessment**: Color-coded risk levels (green/amber/red) based on remaining days
- **Data Export**: CSV, PDF, and GDPR-compliant DSAR exports
- **Excel Import**: Bulk trip import from Excel workbooks
- **Audit Logging**: Comprehensive audit trail for all operations
- **Security**: Argon2 password hashing, session management, rate limiting
- **GDPR Compliance**: Data retention policies, DSAR tools, privacy controls

### 🔒 Security
- Argon2 password hashing (industry-standard)
- Session security with HTTPOnly cookies
- Rate limiting on authentication endpoints
- Input validation and sanitization
- SQL injection prevention via parameterized queries
- Security headers (XSS protection, frame options, content type)

### 🧹 Cleanup
- Removed obsolete test bypass files
- Removed empty/experimental directories
- Consolidated changelog documentation
- Standardized file structure

### 📚 Documentation
- Comprehensive README with setup instructions
- Installation guide (INSTALL.md)
- Testing documentation (TESTING.md)
- GDPR compliance notice
- Logic explanation document
- Security audit documentation
- Schema documentation
- Deployment and rollback procedures

---

## [1.6.4] - 2025-01-28

### Fixed
- Calendar display bug where trip blocks were invisible
- JavaScript timing issues with DOM layout calculation
- Statistics display showing zeros

### Added
- Trip reassignment feature (drag-and-drop between employees)
- Mobile touch support for calendar interactions
- Comprehensive test suite at `/calendar_test`

### Improved
- Enhanced console logging for debugging
- Better error handling for missing DOM elements
- Conflict validation for trip overlaps

---

## [1.6.3] - 2025-01-29

### Changed
- Project cleanup and organization
- Removed cache and temporary files
- Consolidated log files
- Organized backup structure

---

## [1.6.2] - 2025-01-28

### Fixed
- Critical calendar display bug
- ReferenceError with colorClass variable
- DOM layout timing issues
- Statistics calculation

### Added
- Trip reassignment functionality
- Mobile touch support
- Comprehensive test suite

---

## [1.5.0] - 2024-10-20

### Added
- Automatic backup system (startup/shutdown)
- Windows deployment batch files
- Enhanced error pages (404/500)
- Comprehensive test suite
- GDPR compliance enhancements

### Security
- Password complexity requirements
- Enhanced session security
- Rate limiting
- Security headers

### Improved
- User interface polishing
- Help system
- Export functionality
- Database schema with indexes

---

## [1.1] - 2024-10

### Security Improvements
- Argon2/bcrypt password hashing (replaced SHA256)
- Password complexity requirements
- Enhanced session cookie settings
- Security headers
- Input validation and sanitization

### GDPR Compliance
- Data minimization
- Privacy controls
- Enhanced DSAR tools
- Retention policy enforcement

---

## [1.0] - 2024-09

### Initial Release
- Employee management
- Trip logging
- 90/180-day rule compliance tracking
- Excel import functionality
- Calendar view
- GDPR compliance tools
- Audit logging
- Export functionality (CSV, PDF, ZIP)

---

**Note**: This changelog consolidates all previous changelog files (CHANGELOG_PRODUCTION.md, CHANGELOG_v1.6.2.md, CHANGELOG_v1.6.3_cleanup.md) into a single authoritative record.

