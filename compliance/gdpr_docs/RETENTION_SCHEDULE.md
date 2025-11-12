# Data Retention Schedule
## ComplyEur - EU Trip Tracker

**Version:** 1.0  
**Date:** 2025-01-XX  
**Review Date:** Annual (or as required by law)

---

## Overview

This Data Retention Schedule outlines how long personal data is retained by ComplyEur and the procedures for secure deletion. This schedule complies with GDPR Article 5(1)(e) (storage limitation principle).

---

## Retention Principles

1. **Storage Limitation:** Personal data shall not be kept longer than necessary
2. **Lawful Basis:** Retention periods are based on legal obligations and legitimate business needs
3. **Automatic Deletion:** Data is automatically purged after retention period expires
4. **Secure Deletion:** Deleted data cannot be recovered

---

## Data Categories and Retention Periods

### 1. Employee Data

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|-----------------|------------|-----------------|
| Employee Name | 36 months after last trip exit date | Legal obligation (Schengen compliance) | Automatic purge |
| Trip Records | 36 months after trip exit date | Legal obligation (Schengen compliance) | Automatic purge |
| Entry/Exit Dates | 36 months after trip exit date | Legal obligation (Schengen compliance) | Automatic purge |
| Trip Purpose | 36 months after trip exit date | Legitimate interest (HR management) | Automatic purge |

**Calculation:** Retention period starts from the **exit_date** of each trip. If no exit_date exists, retention starts from **entry_date + 365 days** (assumed 1-year trip).

**Default Period:** 36 months (3 years) - configurable via admin settings

**Minimum Period:** 12 months (legal requirement for travel records)

**Maximum Period:** 60 months (5 years) - only if required by specific legal obligation

---

### 2. Admin Access Data

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|-----------------|------------|-----------------|
| Session Cookies | Session duration (30 min idle timeout) | Legitimate interest (security) | Automatic expiry |
| Login Logs | 90 days | Legitimate interest (security) | Automatic rotation |
| Audit Logs | Indefinite (immutable) | Legal obligation (compliance audit) | Manual review only |
| IP Addresses (in audit logs) | Indefinite (as part of audit trail) | Legal obligation (compliance audit) | Manual review only |

**Note:** Audit logs are retained indefinitely for compliance and security purposes. These logs are:
- Immutable (hash-verified)
- Do not contain personal data (only masked identifiers)
- Required for legal and regulatory compliance

---

### 3. Export Files

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|-----------------|------------|-----------------|
| DSAR Exports (ZIP) | 30 days after generation | Legitimate interest (data subject rights) | Manual deletion |
| CSV Exports | 30 days after generation | Legitimate interest (data subject rights) | Manual deletion |
| PDF Reports | 30 days after generation | Legitimate interest (data subject rights) | Manual deletion |

**Storage Location:** `./exports/` directory (local filesystem)

**Deletion:** Manual deletion by administrator (not automated)

---

### 4. Backup Data

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|-----------------|------------|-----------------|
| Daily Backups | 30 days | Legitimate interest (data recovery) | Automatic rotation |
| Weekly Backups | 12 weeks | Legitimate interest (data recovery) | Automatic rotation |
| Monthly Backups | 12 months | Legitimate interest (data recovery) | Automatic rotation |

**Backup Location:** `./backups/` directory (encrypted)

**Format:** AES-256-GCM encrypted SQLite backups

**Deletion:** Automatic rotation based on retention policy

---

### 5. Log Files

| Data Type | Retention Period | Legal Basis | Deletion Method |
|-----------|-----------------|------------|-----------------|
| Application Logs | 90 days | Legitimate interest (troubleshooting) | Automatic rotation |
| Security Logs | 1 year | Legal obligation (security audit) | Automatic rotation |
| SIEM Logs | 90 days | Legitimate interest (security monitoring) | Automatic rotation |
| Integrity Hashes | Indefinite | Legal obligation (compliance audit) | Manual review only |

**Log Rotation:** Automatic (10 MB per file, 5 backups)

---

## Retention Period Calculation

### For Trip Records

```python
retention_date = exit_date + retention_months
# or if no exit_date:
retention_date = entry_date + 365 days + retention_months
```

### For Employee Records

```python
# Employee retention = latest trip retention date
latest_trip_retention = max(all_trip_retention_dates)
employee_retention = latest_trip_retention
```

---

## Deletion Procedures

### 1. Automatic Purge

**Trigger:** Scheduled job (daily) or manual trigger

**Process:**
1. Calculate retention cutoff date
2. Identify expired trips (exit_date < cutoff)
3. Identify employees with no remaining trips
4. Delete expired trips (cascade delete)
5. Delete employees with no trips
6. Log deletion in audit trail
7. Verify deletion (confirmation log)

**Audit Logging:**
- Number of trips deleted
- Number of employees deleted
- Cutoff date used
- Timestamp of purge

### 2. Manual Deletion (DSAR)

**Trigger:** Data subject request (Right to Erasure)

**Process:**
1. Verify request legitimacy
2. Export data for data subject (if requested)
3. Delete employee and all associated trips
4. Confirm deletion in writing
5. Log deletion in audit trail

**Audit Logging:**
- Employee ID deleted
- Employee name (for audit)
- Number of trips deleted
- Reason: "DSAR - Right to Erasure"
- Requesting admin identifier

### 3. Secure Deletion

**Method:**
- SQLite: DELETE statement (permanent deletion)
- Files: Secure overwrite (if possible) or immediate deletion
- Backups: Deleted during backup rotation

**Verification:**
- Database query to confirm deletion
- File system check for export files
- Integrity check of audit logs

---

## Exceptions and Extensions

### Legal Hold

If legal proceedings require data retention:
- **Process:** Mark data as "legal hold"
- **Extension:** Retain until legal proceedings conclude
- **Review:** Annual review of legal holds
- **Documentation:** Record reason and expected end date

### Regulatory Investigation

If regulatory authority requests data retention:
- **Process:** Mark data as "regulatory hold"
- **Extension:** Retain until investigation concludes
- **Notification:** Notify data subjects if required
- **Documentation:** Record authority and investigation details

---

## Review and Updates

### Review Schedule

- **Annual Review:** Full retention schedule review
- **Legal Updates:** Review when data protection laws change
- **Business Changes:** Review when business requirements change

### Approval

This retention schedule must be approved by:
- Data Protection Officer (if applicable)
- Compliance Officer
- Legal Counsel
- Management

**Current Approval:**

Name: _________________________  
Title: _________________________  
Signature: _________________________  
Date: _________________________

---

## Compliance

This retention schedule ensures compliance with:

- **GDPR Article 5(1)(e):** Storage limitation
- **GDPR Article 17:** Right to erasure
- **GDPR Article 30:** Records of processing activities
- **UK GDPR:** Equivalent provisions

---

## Questions

For questions about this retention schedule:

**Contact:** [Data Protection Officer Email]  
**Review Date:** [Annual Review Date]

---

**Last Updated:** 2025-01-XX  
**Next Review:** 2026-01-XX

