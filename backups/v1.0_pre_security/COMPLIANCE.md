# GDPR Compliance Guide - EU Trip Tracker

## Overview

The EU Trip Tracker is designed to comply with GDPR requirements for a small, local-only system that processes minimal personal data for EU travel compliance tracking. This document explains the system's GDPR features, data handling practices, and operational procedures.

---

## 1. Data We Store

### Personal Data
- **Employee Name**: The only identifiable personal data
- **Trip Records**: Country code, entry date, exit date, travel days, creation timestamp

### What We DON'T Store
- ❌ Email addresses, phone numbers
- ❌ Home addresses or location data
- ❌ Financial information
- ❌ Health data or biometrics
- ❌ Special category data (race, religion, political opinions, etc.)
- ❌ Employment details beyond name
- ❌ Analytics, tracking, or profiling data

---

## 2. Purpose and Lawful Basis

### Purpose
To track compliance with the Schengen 90/180-day rule for business travel, preventing legal violations.

### Lawful Basis
- **Employee data**: Legitimate Interests (business compliance tracking)
- **Trip data**: Legal Obligation (Schengen regulation compliance)

We do NOT rely on consent. No consent banners are required.

---

## 3. Data Minimisation

The system implements strict data minimisation principles:
- Only essential fields stored (name + trip dates)
- No contact information
- No employment details
- No optional or "nice to have" fields
- Local-only storage (no cloud, no third parties)

---

## 4. Security Measures

### Access Control
- Admin-only access via password-protected login
- Strong password hashing (Argon2 preferred, bcrypt fallback)
- Session idle timeout (default: 30 minutes, configurable)
- Login rate limiting (5 attempts per 10 minutes)

### Session Security
- HttpOnly cookies (not accessible via JavaScript)
- SameSite=Strict (CSRF protection)
- Secure flag (when HTTPS enabled)
- No tracking or analytics cookies

### Database Security
- Foreign key constraints with CASCADE delete
- Indexes on employee_id and exit_date
- SQLite file permissions (local filesystem only)
- No external API calls or SDKs

### Audit Logging
- All admin actions logged (login, export, delete, purge, settings)
- Timestamps and masked admin identifiers
- No passwords or sensitive data in logs
- Log path: `./logs/audit.log`

---

## 5. Retention Policy

### Default Retention
- **Trips**: 36 months after exit_date (configurable via `RETENTION_MONTHS`)
- **Employees**: Automatically deleted when no trips remain

### Retention Purge
Trips past the retention period are deleted via:
- Manual purge (Admin → Privacy Tools → Run Purge)
- Or scheduled job (if implemented)

### Configuration
Update retention period: **Admin → Settings → Retention Period**

---

## 6. Data Subject Rights (DSAR)

The system provides full GDPR data subject rights via **Admin → Privacy Tools**:

### 📥 Right to Access
- Generate a ZIP export containing:
  - `employee.json` (name, ID, timestamp)
  - `trips.csv` (all trip records)
  - `processing-notes.txt` (purpose, lawful basis, rights info)
- Download link provided immediately

### ✏️ Right to Rectification
- Update employee name via Privacy Tools
- Admin can also manually edit trips in employee detail view

### 🗑️ Right to Erasure ("Right to be Forgotten")
- Hard delete employee + all trips
- Confirmation required (irreversible)
- Audit logged

### 🔒 Right to Restriction of Processing (Anonymization)
- Replace name with "Employee #XXXX"
- Keeps trip data for aggregate compliance tracking
- Reversible (admin can update name again)

### 📤 Right to Data Portability
- Included in DSAR export (JSON + CSV formats)

### ⛔ Right to Object
- Contact admin to discuss concerns
- Admin can anonymize or delete data

### ℹ️ Right to Be Informed
- `/privacy` page provides full transparency
- "Explain Processing" button in Privacy Tools

---

## 7. Operational Procedures

### For Administrators

#### Daily Operations
1. **Login**: Use admin password at `/login`
2. **Manage Trips**: Add/edit/delete via dashboard and employee detail views
3. **Monitor Compliance**: Dashboard shows color-coded status (green/yellow/red)

#### DSAR Requests
When an employee requests access to their data:

1. Navigate to **Admin → Privacy Tools**
2. Search for the employee by name
3. Click **Export Data (ZIP)**
4. Download the ZIP file and provide to the employee
5. File saved in `./exports/` directory

#### Deletion Requests
When an employee requests data deletion:

1. Navigate to **Admin → Privacy Tools**
2. Search for the employee
3. Click **Delete Employee**
4. Confirm deletion (this is irreversible)
5. Action is audit logged

#### Rectification Requests
When an employee requests name correction:

1. Navigate to **Admin → Privacy Tools**
2. Search for the employee
3. Click **Rectify Name**
4. Enter corrected name and confirm

#### Anonymization
To anonymize an employee while keeping trip data:

1. Navigate to **Admin → Privacy Tools**
2. Search for the employee
3. Click **Anonymize**
4. Name replaced with "Employee #XXXX"

### Retention Purge

#### Manual Purge
1. Navigate to **Admin → Privacy Tools**
2. Review "Trips Pending Deletion" count
3. Click **Run Retention Purge Now**
4. Confirm purge
5. Result shows trips/employees deleted

#### Scheduled Purge (Optional)
Implement a cron job or scheduled task:

```bash
# Example: Run monthly purge
# Add this to crontab or Task Scheduler
# Requires a CLI script (not included by default)
0 0 1 * * python /path/to/purge_script.py
```

### Settings Management

Navigate to **Admin → Settings** to configure:

- **Retention Period**: How long to keep trips (months)
- **Session Timeout**: Idle timeout before auto-logout (minutes)
- **Password Scheme**: Argon2 (recommended) or bcrypt
- **Export Directory**: Where DSAR exports are saved
- **Audit Log Path**: Where audit logs are stored
- **Secure Cookies**: Enable for HTTPS (disable for local HTTP)

Click **Save Settings** to apply changes (requires restart for some settings).

### Changing Admin Password

1. Navigate to **Admin → Settings**
2. Scroll to "Change Admin Password"
3. Enter new password (minimum 8 characters recommended)
4. Click **Change Password**
5. You'll be logged out; log in with new password

---

## 8. Exports and Reports

### CSV Export
**Dashboard or Employee Detail** → Export button
- All trips or employee-specific trips
- Columns: Employee Name, Country, Entry Date, Exit Date, Travel Days

### PDF Reports
- **Employee Report**: Individual compliance report with trip history
- **Summary Report**: All employees with days used and status
- Color-coded status indicators

### DSAR ZIP Export
**Admin → Privacy Tools** → Export Data
- Complete data package for data subject requests
- Includes JSON, CSV, and processing notes

---

## 9. Privacy Policy

### Public Access
The privacy policy is accessible at: `/privacy`
- No login required (transparency)
- Explains all data processing
- Lists all GDPR rights
- Includes contact information for DPA complaints

### Content
The policy covers:
- What data we store (and don't store)
- Why we process it (purpose and lawful basis)
- How long we keep it (retention policy)
- How we secure it (security measures)
- Your rights (DSAR, rectification, erasure, etc.)
- No tracking, no third parties, no transfers
- No automated decision-making or profiling

---

## 10. Backup and Restore

### What to Back Up
For full system recovery, back up these files/directories:

```
/eu_tracker.db          # Main database
/exports/               # DSAR exports
/logs/                  # Audit logs
/compliance/            # Data map
/settings.json          # Configuration
```

### Backup Procedure
1. Stop the application
2. Copy the above files/directories to a secure location
3. Use encrypted storage for backups (personal data)
4. Restart the application

### Restore Procedure
1. Stop the application
2. Copy backed-up files to original locations
3. Verify file permissions
4. Restart the application
5. Test login and data access

### Backup Retention
- Keep backups for same duration as retention policy (36 months)
- Delete old backups securely (overwrite)
- Consider encryption for backup media

---

## 11. Incident Response

### Data Breach
If the database or server is compromised:

1. **Immediately**:
   - Shut down the application
   - Disconnect from network if necessary
   - Assess scope of breach (which data accessed?)

2. **Within 72 hours**:
   - Notify your Data Protection Authority (DPA) if personal data compromised
   - Document the breach: what data, how many employees, when, how

3. **Notify Employees**:
   - If high risk to individuals, notify affected employees directly
   - Provide clear information about what happened and what to do

4. **Remediation**:
   - Fix vulnerability
   - Restore from backup if necessary
   - Review security measures
   - Update passwords

### Data Loss
If database is lost/corrupted:

1. Restore from most recent backup
2. Document the incident in audit log
3. Notify affected employees if data cannot be recovered
4. Review backup procedures

### Unauthorized Access
If someone gains unauthorized admin access:

1. Change admin password immediately
2. Review audit logs for suspicious activity
3. Check for data exports or deletions
4. Notify employees if data was accessed/modified
5. Report to DPA if required

---

## 12. Compliance Checklist

Use this checklist to verify GDPR compliance:

### Data Minimisation
- [ ] Only name + trip dates stored
- [ ] No unnecessary personal data fields
- [ ] No special category data
- [ ] No profiling or analytics

### Lawful Basis
- [ ] Purpose documented (Schengen compliance)
- [ ] Lawful basis identified (Legitimate Interests / Legal Obligation)
- [ ] No reliance on consent

### Security
- [ ] Strong password hashing (Argon2/bcrypt)
- [ ] Session timeout configured
- [ ] Login rate limiting active
- [ ] HttpOnly + SameSite=Strict cookies
- [ ] No external API calls or SDKs
- [ ] Audit logging enabled

### Retention
- [ ] Retention policy configured (default 36 months)
- [ ] Manual or automated purge process in place
- [ ] Old data deleted regularly

### Data Subject Rights
- [ ] DSAR export available (ZIP with JSON, CSV, TXT)
- [ ] Rectification process available
- [ ] Erasure (deletion) available
- [ ] Anonymization available
- [ ] Privacy policy accessible at `/privacy`

### Transparency
- [ ] Privacy policy complete and accurate
- [ ] Data map documented (`compliance/data_map.yaml`)
- [ ] Audit logs capture all admin actions
- [ ] No hidden data collection

### Backup & Recovery
- [ ] Regular backups scheduled
- [ ] Backup includes all critical files
- [ ] Restore procedure tested
- [ ] Backups encrypted and secured

---

## 13. Third-Party Dependencies

### Python Packages
The system uses the following third-party packages:

- **Flask**: Web framework (BSD license)
- **openpyxl**: Excel parsing (MIT license)
- **argon2-cffi**: Password hashing (MIT license)
- **reportlab**: PDF generation (BSD license)
- **pandas**: Data processing (BSD license)

### Compliance Notes
- No packages phone home or collect telemetry
- No CDNs or external fonts (all assets bundled)
- No analytics or tracking libraries
- No third-party APIs

---

## 14. Limitations and Disclaimers

### This System Is NOT
- ❌ A legal advice tool
- ❌ A guarantee of Schengen compliance
- ❌ A replacement for professional immigration advice
- ❌ Certified or audited by a third party

### Administrator Responsibilities
The administrator is responsible for:
- Keeping admin password secure
- Responding to DSAR requests promptly (within 30 days)
- Running retention purges regularly
- Backing up data
- Notifying DPA of breaches (within 72 hours)
- Keeping the privacy policy accurate

### Data Controller
The organization running this system is the **Data Controller** under GDPR and is responsible for compliance.

---

## 15. Updates and Maintenance

### Software Updates
- Check for updates regularly
- Review changelog for security fixes
- Test updates in a non-production environment first
- Back up before applying updates

### Configuration Changes
- Document all settings changes
- Test impact on existing data
- Notify employees if retention policy changes

### Privacy Policy Updates
- Update `/privacy` page if data processing changes
- Update "Last Updated" date
- Notify employees of significant changes (optional but recommended)

---

## 16. Getting Help

### For Technical Issues
- Review logs in `./logs/audit.log`
- Check database integrity with SQLite tools
- Verify file permissions
- Restart the application

### For GDPR Questions
- Consult your Data Protection Officer (DPO) if applicable
- Review official GDPR guidance: https://gdpr.eu/
- Contact your local Data Protection Authority
- Seek legal advice for complex cases

### For Data Subject Requests
- Use the Privacy Tools interface for most requests
- Respond within 30 days (GDPR requirement)
- Document all requests and responses
- No fee for first request (can charge for repeated/excessive requests)

---

## 17. Quick Reference

### Key Files and Directories
```
eu_tracker.db                  # Main database (SQLite)
settings.json                  # Configuration file
compliance/data_map.yaml       # Data processing map
logs/audit.log                 # Audit log
exports/                       # DSAR exports
templates/privacy.html         # Public privacy policy
```

### Key URLs
```
/login                         # Admin login
/dashboard                     # Main dashboard
/privacy                       # Public privacy policy (no login)
/admin/privacy-tools           # DSAR and retention tools
/admin/settings                # Configuration
```

### Default Credentials
```
Username: (not required, single admin)
Password: admin123
⚠️ Change this immediately after first login!
```

### Default Settings
```
RETENTION_MONTHS: 36
SESSION_IDLE_TIMEOUT_MINUTES: 30
PASSWORD_HASH_SCHEME: argon2
DSAR_EXPORT_DIR: ./exports
AUDIT_LOG_PATH: ./logs/audit.log
SESSION_COOKIE_SECURE: false (enable for HTTPS)
```

---

## 18. Testing Checklist

Before deploying to production:

### Functionality Tests
- [ ] Login works with correct password
- [ ] Login fails with incorrect password
- [ ] Session timeout works after idle period
- [ ] Add/edit/delete employee works
- [ ] Add/edit/delete trip works
- [ ] Days calculation accurate
- [ ] Dashboard shows correct status (green/yellow/red)

### GDPR Tests
- [ ] DSAR export creates valid ZIP
- [ ] ZIP contains employee.json, trips.csv, processing-notes.txt
- [ ] Delete employee removes all trips
- [ ] Rectify name updates correctly
- [ ] Anonymize replaces name
- [ ] Privacy policy loads without login
- [ ] Retention purge deletes old trips
- [ ] Audit log captures actions

### Security Tests
- [ ] Cannot access dashboard without login
- [ ] Rate limiting blocks after 5 failed logins
- [ ] Session expires after timeout
- [ ] Cookies are HttpOnly and SameSite=Strict
- [ ] No external network requests made

---

## Conclusion

The EU Trip Tracker is designed with "privacy by design" principles:
- **Minimal data**: Only what's necessary
- **Local storage**: No cloud, no transfers
- **Full transparency**: Privacy policy and data map
- **All GDPR rights**: Access, rectify, delete, export
- **Strong security**: Password hashing, session management, audit logging
- **Automatic retention**: Old data deleted per policy

For questions or concerns, contact your system administrator or Data Protection Officer.

**Remember**: GDPR compliance is an ongoing responsibility, not a one-time setup. Regularly review data, respond to requests promptly, and keep the system updated.