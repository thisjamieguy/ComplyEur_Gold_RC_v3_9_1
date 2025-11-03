# ComplyEur Employee EU Travel Tracker

## Version 1.1 (Post-Security Review) - October 2025
### 🔒 Security Improvements
- **Password Security:**
  - Implemented Argon2/bcrypt password hashing (replaced SHA256)
  - Added password complexity requirements (minimum 8 characters, letters + numbers)
  - Secure password storage using environment variables
  - Password upgrade mechanism for legacy hashes

- **Session & Cookie Security:**
  - Persistent secret key from environment variables (replaced os.urandom)
  - Enhanced session cookie settings (HttpOnly, SameSite=Lax, Secure for HTTPS)
  - Configurable session timeout (default 30 minutes)
  - Added security headers (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS)

- **Input Validation:**
  - Comprehensive validation for employee names (sanitization, length, character checks)
  - Date validation with reasonable range checks (10 years past, 2 years future)
  - Country code validation against whitelist
  - Date range validation (exit date must be after entry date, max 2 year duration)
  - SQL injection prevention through parameterized queries

- **Database & Endpoint Security:**
  - Removed insecure debug routes (`/clear_imported_trips`)
  - Debug mode controlled via environment variable (disabled by default)
  - Database path configurable via environment
  - Enhanced audit logging for all critical operations

- **Configuration Management:**
  - All secrets and configuration in `.env` file (not hardcoded)
  - Template file provided (`env_template.txt`)
  - Automatic secret key generation with warnings if not configured
  - Environment-based deployment configuration

### ⚖️ GDPR Compliance Enhancements
- **Data Minimization:**
  - Only essential data stored (name, country, dates)
  - No unnecessary personal identifiers

- **Privacy Controls:**
  - Added "Delete All Data" functionality in admin settings
  - Confirmation required for destructive operations
  - Automated deletion of export files with data purge
  - Clear privacy notice in footer: "All data processed locally"

- **User Rights:**
  - Enhanced DSAR (Data Subject Access Request) tools
  - Employee data export (ZIP with JSON)
  - Employee data deletion with audit trail
  - Data rectification capabilities
  - Retention policy enforcement (configurable months)

### 📦 Export & Backup Safety
- **Local-Only Processing:**
  - All CSV/PDF exports write to local disk only
  - No automatic email or cloud upload
  - Export files served as direct downloads
  - DSAR exports stored in configurable local directory

### 🔧 Technical Improvements
- **Dependencies:**
  - Added `python-dotenv==1.0.0` for environment management
  - Updated `bcrypt==4.1.2`
  - All dependencies version-pinned for security

- **Code Quality:**
  - Comprehensive error handling with user-friendly messages
  - Audit logging for all data modifications
  - Improved flash messages for user feedback
  - Better separation of concerns

### 📝 Documentation
- Created `env_template.txt` with all configuration options
- Enhanced startup messages with configuration summary
- Security warnings for debug mode and missing .env
- GDPR compliance notice in UI footer

---

## Version 1.0 (Pre-Security) - September 2025
- Fully working MVP build
- Trip logging, 90/180 calculation, and Excel import functional
- Weekly calendar view added
- Default colours set to match ComplyEur brand
- Basic authentication implemented
- Session management in place

### Features Implemented
- Employee management and trip logging
- Schengen 90/180-day rule compliance tracking
- Excel import functionality for bulk data entry
- Calendar view for trip visualization
- GDPR compliance tools (DSAR operations)
- Data retention and purge functionality
- Admin settings and configuration
- Audit logging for all operations
- Export functionality (CSV, PDF, ZIP)

### Technical Details
- Flask web application
- SQLite database backend
- Responsive UI with HubSpot-style design
- Session management and authentication
- File upload handling
- GDPR-compliant data processing
