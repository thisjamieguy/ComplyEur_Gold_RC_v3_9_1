# GDPR Compliance Notice

**ComplyEur - Version 3.9.1**  
**Last Updated**: 2025-11-12

---

## Overview

ComplyEur is designed with privacy and GDPR compliance as core principles. This document outlines how we handle personal data in accordance with UK GDPR and EU GDPR requirements.

---

## Data Controller

**Controller**: Your Organisation (the entity using ComplyEur)  
**Purpose**: Track employee compliance with the EU 90/180-day Schengen travel rule  
**Storage Location**: Local SQLite database on your system (no cloud storage)

---

## Personal Data We Process

### Minimal Data Collection

ComplyEur follows the principle of **data minimization**. We only collect and store:

1. **Employee Name** (text field)
   - Purpose: Identify employees for compliance reporting
   - Lawful Basis: Legitimate Interests (business compliance tracking)
   - Retention: Deleted automatically when no trips remain, or 36 months after last trip exit date

2. **Trip Dates** (entry_date, exit_date)
   - Purpose: Calculate days spent in Schengen area
   - Lawful Basis: Legal Obligation (Schengen 90/180-day rule compliance)
   - Retention: 36 months after exit_date (configurable)

3. **Country Codes** (2-letter ISO codes, e.g., FR, DE, IT)
   - Purpose: Track which Schengen country visited
   - Lawful Basis: Legal Obligation
   - Retention: 36 months after exit_date

### What We Do NOT Collect

- ❌ Email addresses
- ❌ Phone numbers
- ❌ Home addresses
- ❌ Passport numbers
- ❌ Employment details beyond name
- ❌ Financial information
- ❌ Health data
- ❌ Biometric data
- ❌ Tracking cookies or analytics
- ❌ Third-party data sharing

---

## Data Storage and Security

### Local-Only Storage

- All data is stored **locally** on your system
- No data is transmitted to external servers
- No cloud storage or third-party services
- No cookies beyond essential session management

### Security Measures

- **Password Hashing**: Argon2 industry-standard hashing (passwords never stored in plaintext)
- **Session Security**: HTTPOnly cookies, SameSite=Strict, Secure flag for HTTPS
- **Access Control**: Admin-only access (no public endpoints)
- **Audit Logging**: Comprehensive audit trail for all operations
- **Rate Limiting**: Protection against brute-force attacks
- **Input Validation**: All user input validated and sanitized

### Database Security

- SQLite database with foreign key constraints
- Encrypted backups available (optional)
- Automatic data retention and purging
- CASCADE delete ensures data consistency

---

## Your Rights Under GDPR

As a data subject, you have the following rights:

### 1. Right to Access (Article 15)

**DSAR Export Tool**: ComplyEur includes a built-in Data Subject Access Request (DSAR) export feature.

- Navigate to: Employee → Actions → Export Data
- Generates a ZIP file containing:
  - `employee.json` - Employee name and metadata
  - `trips.csv` - All trip records
  - `processing-notes.txt` - Purpose, lawful basis, and rights information

### 2. Right to Rectification (Article 16)

- Employee names can be updated at any time
- Navigate to: Employee → Edit → Update Name

### 3. Right to Erasure (Article 17)

- Full employee deletion available
- Navigate to: Employee → Actions → Delete Employee
- **Warning**: This permanently deletes all associated trip data
- Audit log records all deletions

### 4. Right to Data Portability (Article 20)

- Export data in machine-readable formats (CSV, JSON)
- CSV export available for all trips
- DSAR export includes JSON format

### 5. Right to Object (Article 21)

- Contact your system administrator
- Data processing can be stopped (employee deletion)

### 6. Right to Restrict Processing (Article 18)

- Contact your system administrator
- Employee records can be marked inactive

---

## Data Retention

### Automatic Retention Policy

- **Default**: 36 months after trip exit date
- **Configurable**: Admin can adjust retention period in Settings
- **Automatic Purging**: Expired trips are automatically deleted
- **Employee Deletion**: Employees are deleted when no trips remain

### Manual Deletion

- Admin can manually delete employees and trips at any time
- All deletions are logged in the audit trail

---

## Cookies and Tracking

### Essential Cookies Only

ComplyEur uses **one essential cookie**:

- **Name**: `session`
- **Purpose**: Admin authentication and session management
- **Type**: Essential (no consent required under GDPR)
- **Expiry**: Configurable (default 30 minutes idle timeout)
- **Security**: HttpOnly, SameSite=Strict, Secure (when HTTPS enabled)
- **Data Stored**: Session ID only (no personal data in cookie)

### No Tracking Cookies

- ❌ No analytics cookies
- ❌ No advertising cookies
- ❌ No third-party tracking
- ❌ No social media cookies

---

## Third-Party Sharing

**None**. ComplyEur does not share data with any third parties.

- No cloud services
- No external APIs (except optional news feeds, which don't transmit personal data)
- No analytics services
- No advertising networks

---

## Data Breach Procedures

In the unlikely event of a data breach:

1. **Immediate Action**: Secure the system and assess the scope
2. **Notification**: Notify affected individuals within 72 hours (if required)
3. **Documentation**: Record the breach in audit logs
4. **Remediation**: Take steps to prevent future breaches

**Note**: As ComplyEur stores data locally, breach risk is minimal. Physical access controls are the primary security measure.

---

## Lawful Basis for Processing

### Legitimate Interests (Article 6(1)(f))

- **Employee Names**: Business compliance tracking
- **Purpose**: Ensure employees comply with EU 90/180-day rule
- **Necessity**: Required for legal compliance and business operations

### Legal Obligation (Article 6(1)(c))

- **Trip Dates and Countries**: Schengen 90/180-day rule compliance
- **Purpose**: Track and calculate days spent in Schengen area
- **Necessity**: Required to comply with EU immigration rules

---

## Special Category Data

**None**. ComplyEur does not process any special category personal data as defined in Article 9 of GDPR:

- ❌ No racial or ethnic origin
- ❌ No political opinions
- ❌ No religious beliefs
- ❌ No health data
- ❌ No biometric data
- ❌ No sexual orientation

---

## International Transfers

**None**. All data is stored locally on your system. No data is transferred outside the UK/EU.

---

## Contact Information

For GDPR-related inquiries:

1. **Contact your system administrator** (the person who manages ComplyEur)
2. **Use DSAR export tool** for data access requests
3. **Review audit logs** for data processing history

---

## Compliance Statement

ComplyEur is designed to be GDPR-compliant by default:

✅ **Data Minimization**: Only essential data collected  
✅ **Purpose Limitation**: Data used only for compliance tracking  
✅ **Storage Limitation**: Automatic retention and purging  
✅ **Accuracy**: Data can be rectified at any time  
✅ **Security**: Industry-standard security measures  
✅ **Transparency**: Clear privacy notices and documentation  
✅ **Accountability**: Comprehensive audit logging  

---

## Updates to This Notice

This GDPR notice may be updated periodically. The "Last Updated" date at the top indicates when changes were made.

**Version History**:
- 3.9.1 (2025-11-12) - Gold Release Candidate documentation

---

## Additional Resources

- `compliance/data_map.yaml` - Detailed data processing map
- `compliance/gdpr_docs/` - Additional GDPR documentation
- `docs/security_audit.md` - Security audit report
- `docs/schema_summary.md` - Database schema documentation

---

**Privacy-First Design**: ComplyEur is built with privacy and GDPR compliance as core principles. We believe in minimal data collection, local-only storage, and full user control.

---

*This notice is provided for informational purposes. For legal advice on GDPR compliance, consult with a qualified legal professional.*

