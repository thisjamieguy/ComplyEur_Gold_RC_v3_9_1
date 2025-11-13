# Security Audit Report — Privacy Policy Compliance
## ComplyEur v1.0.0 Post MVP

**Date:** 2025-01-XX  
**Purpose:** Verify all security measures listed in the privacy policy are correctly implemented

---

## Executive Summary

This audit compares the security measures claimed in the privacy policy (`compliance/gdpr_docs/PRIVACY_POLICY.md`) against the actual implementation in the codebase. **4 issues found** that need to be addressed.

---

## Security Measures Audit

### 1. ✅ Password-Protected Admin Access with Strong Hashing (Argon2/bcrypt)

**Status:** ✅ **FULLY IMPLEMENTED**

**Evidence:**
- `app/services/hashing.py` — Implements Argon2 with bcrypt fallback
- `app/modules/auth/password.py` — Enterprise password management with Argon2id
- `app/config_auth.py` — Configurable Argon2 parameters (memory, time, parallelism)

**Implementation Details:**
```python
# app/services/hashing.py
class Hasher:
    def __init__(self, scheme: Literal['argon2', 'bcrypt'] = 'argon2'):
        # Prefers Argon2, falls back to bcrypt
```

**Verdict:** ✅ Compliant — Strong password hashing is properly implemented.

---

### 2. ⚠️ Session Idle Timeout (30 minutes)

**Status:** ⚠️ **MISMATCH — NEEDS FIXING**

**Privacy Policy Claims:**
- "30 minutes idle timeout (configurable)"

**Actual Implementation:**
- `app/config_auth.py` line 45: Default is **15 minutes**, not 30
```python
IDLE_TIMEOUT = timedelta(minutes=int(os.getenv("IDLE_TIMEOUT_MINUTES", 15)))
```

**Other References:**
- `app/__init__auth__.py` sets default to 30 minutes in some configs
- `config.py` default is 30 minutes
- Privacy policy template shows `{{ session_timeout_minutes }}` (dynamic)

**Issue:** The default timeout in the main auth config is 15 minutes, but the privacy policy states 30 minutes.

**Recommendation:** Change the default in `app/config_auth.py` from 15 to 30 minutes, or update the privacy policy to reflect 15 minutes (with note that it's configurable).

---

### 3. ⚠️ Login Rate Limiting (max 5 attempts per 5 minutes)

**Status:** ⚠️ **MISMATCH — NEEDS CLARIFICATION**

**Privacy Policy Claims:**
- "Login rate limiting (max 5 attempts per 5 minutes)"

**Actual Implementation:**
- `app/config_auth.py` line 41: `RATE_PER_IP = "5 per minute"` (stricter than policy)
- `app/config_auth.py` line 42: `RATE_PER_USERNAME = "10 per 15 minutes"`

**Issue:** The policy says "5 attempts per 5 minutes", but the code implements "5 attempts per minute" (which is actually stricter). However, this creates a discrepancy between policy and implementation.

**Recommendation:** Either:
1. Update the privacy policy to say "5 attempts per minute" (more accurate)
2. Change the config to "5 per 5 minutes" to match the policy

**Note:** The current implementation is more secure (stricter), but the policy should match reality.

---

### 4. ⚠️ HttpOnly and SameSite=Strict Session Cookies

**Status:** ⚠️ **PARTIALLY INCONSISTENT**

**Privacy Policy Claims:**
- "HttpOnly and SameSite=Strict session cookies"

**Actual Implementation:**

**Location 1 — `app/config_auth.py` (Auth System):**
```python
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"  # ✅ Correct
```

**Location 2 — `app/__init__.py` (Main App):**
```python
SESSION_COOKIE_HTTPONLY=True,
SESSION_COOKIE_SAMESITE='Lax',  # ⚠️ Should be 'Strict'
```

**Issue:** There are two different session cookie configurations:
- The auth system uses `SameSite=Strict` ✅
- The main app uses `SameSite=Lax` ⚠️

**Recommendation:** Update `app/__init__.py` to use `SameSite='Strict'` for consistency with the privacy policy and the auth system.

---

### 5. ✅ Secure Cookie Support (when HTTPS is enabled)

**Status:** ✅ **FULLY IMPLEMENTED**

**Evidence:**
- `app/config_auth.py` line 20: `SESSION_COOKIE_SECURE` is configurable via environment variable
- `app/__init__.py` line 157: Also configurable
- Both check `os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'`

**Implementation:**
```python
SESSION_COOKIE_SECURE = str(os.getenv("SESSION_COOKIE_SECURE","false")).lower() == "true"
```

**Verdict:** ✅ Compliant — Secure cookies are properly configured and can be enabled when HTTPS is available.

---

### 6. ✅ Audit Logging for All Administrative Actions

**Status:** ✅ **FULLY IMPLEMENTED**

**Evidence:**
- `app/services/audit.py` — Main audit logging service
- `app/services/logging/audit_trail.py` — Immutable audit trail with SHA-256 integrity
- Audit logging is called throughout the codebase for:
  - Login success/failure
  - Logout
  - DSAR operations (export, delete, rectify, anonymize)
  - Trip additions/deletions
  - Settings updates
  - CSV/PDF exports

**Implementation Details:**
- Admin identifiers are masked (SHA256 hash)
- No plaintext passwords logged
- IP addresses captured
- Immutable audit trail with hash chain verification

**Verdict:** ✅ Compliant — Comprehensive audit logging is implemented.

---

### 7. ❌ No External API Calls or Third-Party SDKs

**Status:** ❌ **VIOLATION FOUND**

**Privacy Policy Claims:**
- "No external API calls or third-party SDKs"

**Actual Implementation:**

**External API Calls Found:**

1. **Google reCAPTCHA** (`app/modules/auth/captcha.py`):
   - Line 21: `VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"`
   - Line 83-87: Makes POST requests to Google's API
   - This is an external API call that violates the privacy policy

2. **OAuth Providers** (`app/modules/auth/oauth/providers.py`):
   - Google OAuth: Makes requests to Google's OAuth endpoints
   - Microsoft OAuth: Makes requests to Microsoft's OAuth endpoints
   - These are external API calls

**Note:** These features may be optional/disabled by default, but the code exists and can be enabled.

**Recommendation:**
1. **Option A (Recommended):** Update the privacy policy to clarify:
   - "No external API calls or third-party SDKs (except optional CAPTCHA and OAuth features that can be disabled)"
2. **Option B:** Remove or disable these features entirely to match the policy
3. **Option C:** Document that these are optional security features that require explicit configuration

**Verdict:** ❌ Non-compliant — External API calls exist in the codebase, even if optional.

---

### 8. ⚠️ Foreign Key Constraints with CASCADE Delete (Data Integrity)

**Status:** ⚠️ **MISSING CASCADE CLAUSE**

**Privacy Policy Claims:**
- "Foreign key constraints with CASCADE delete (data integrity)"

**Actual Implementation:**

**Database Schema** (`app/models.py` line 78-92):
```sql
CREATE TABLE IF NOT EXISTS trips (
    ...
    FOREIGN KEY (employee_id) REFERENCES employees (id)
    -- ⚠️ Missing: ON DELETE CASCADE
)
```

**Current Behavior:**
- Foreign keys are defined but **without `ON DELETE CASCADE`**
- The application manually deletes trips when deleting employees (see `app/services/dsar.py` line 185)
- Foreign keys are enabled via `PRAGMA foreign_keys = ON` (verified in tests)

**Issue:** The privacy policy claims CASCADE delete, but the schema doesn't include it. The application handles cascading manually, which works but doesn't match the policy claim.

**Recommendation:** Update the database schema to include `ON DELETE CASCADE`:
```sql
FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
```

**Note:** This requires a database migration for existing installations.

**Verdict:** ⚠️ Partially compliant — Foreign keys exist and work, but CASCADE is not in the schema as claimed.

---

## Summary of Issues

| # | Security Measure | Status | Priority | Action Required |
|---|------------------|--------|----------|-----------------|
| 1 | Password hashing (Argon2/bcrypt) | ✅ Compliant | - | None |
| 2 | Session idle timeout (30 min) | ⚠️ Mismatch | Medium | Fix default timeout or update policy |
| 3 | Rate limiting (5 per 5 min) | ⚠️ Mismatch | Low | Align policy or config |
| 4 | HttpOnly + SameSite=Strict | ⚠️ Inconsistent | Medium | Fix SameSite in main app |
| 5 | Secure cookie (HTTPS) | ✅ Compliant | - | None |
| 6 | Audit logging | ✅ Compliant | - | None |
| 7 | No external APIs | ❌ Violation | High | Document or remove external APIs |
| 8 | Foreign keys + CASCADE | ⚠️ Missing CASCADE | Medium | Add ON DELETE CASCADE to schema |

---

## Recommendations

### High Priority
1. **Document or remove external API calls** (reCAPTCHA, OAuth) to match privacy policy
2. **Fix SameSite cookie inconsistency** — Update `app/__init__.py` to use `'Strict'`

### Medium Priority
3. **Align session timeout default** — Change default to 30 minutes or update policy
4. **Add CASCADE delete to foreign keys** — Update schema and create migration

### Low Priority
5. **Clarify rate limiting** — Update policy to match implementation (5 per minute) or adjust config

---

## Next Steps

1. Review and approve this audit report
2. Prioritise fixes based on business needs
3. Update code or privacy policy to align claims with implementation
4. Test all changes in development environment
5. Update privacy policy version number after changes

---

**Report Generated:** 2025-01-XX  
**Auditor:** AI Security Audit  
**Version:** 1.0

