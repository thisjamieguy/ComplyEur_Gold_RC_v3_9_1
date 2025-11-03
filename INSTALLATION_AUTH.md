# Ultra-Secure Local Admin Login - Installation Guide

## Overview

This is a hardened, local-only admin login system for the EU 90/180 tracker. It provides:
- Argon2id password hashing
- TOTP 2FA (enabled by default)
- Session management with timeouts
- Rate limiting (IP + username)
- Account lockout after failed attempts
- CSRF protection
- Security headers (CSP, HSTS, etc.)

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY to 32+ random bytes
   # Example: SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
   ```

3. **Create first admin user:**
   ```bash
   export FLASK_APP=run_auth.py
   flask admin create --username admin
   ```
   You'll be prompted for a password (minimum 12 characters, must pass strength check).

4. **Run the server:**
   ```bash
   python run_auth.py
   ```
   The server will bind to `127.0.0.1:5001` (local-only).

5. **Access the login:**
   Open `http://127.0.0.1:5001/login` in your browser.

## Setting Up 2FA

After your first login:
1. Visit `/setup-2fa`
2. Scan the QR code with an authenticator app (Google Authenticator, Authy, etc.)
3. Save the secret key in a secure location
4. On subsequent logins, you'll be prompted for the 6-digit code

## CLI Commands

All admin management is done via Flask CLI:

```bash
# Create a new admin user
flask admin create --username <name>

# Reset a user's password
flask admin reset-password --username <name>

# Enable 2FA for a user
flask admin enable-2fa --username <name>

# Disable 2FA for a user
flask admin disable-2fa --username <name>
```

## Security Features

### Password Requirements
- Minimum 12 characters
- Must pass zxcvbn strength check (score >= 3)
- Hashed with Argon2id (configurable parameters)

### Session Security
- HttpOnly cookies
- Secure flag (when enabled)
- SameSite=Strict
- Session ID rotation on login
- 15-minute idle timeout
- 8-hour absolute timeout

### Rate Limiting
- 5 attempts per minute per IP
- 10 attempts per 15 minutes per username
- Account lockout after 5 consecutive failures
- Exponential backoff for repeat offenses

### Account Lockout
- Locked after 5 failed attempts
- Initial lockout: 15 minutes
- Exponential backoff: 2x duration for each additional failure (capped at 24 hours)

### Security Headers
- Content Security Policy (CSP)
- Strict Transport Security (HSTS)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: no-referrer

## File Structure

```
app/
  __init__auth__.py    # Auth app factory
  config_auth.py       # Auth configuration
  security.py          # Password hashing & session utilities
  models_auth.py       # User model (SQLAlchemy)
  routes_auth.py        # Auth routes (login, 2FA, logout)
  forms.py             # Flask-WTF forms
  cli.py               # CLI commands
  utils/
    logger.py          # Auth logging with username redaction
  templates/
    auth_base.html     # Base template
    auth_login.html    # Login & TOTP form
    auth_setup_2fa.html # 2FA setup page
  static/css/
    auth_styles.css    # Auth-specific styles

run_auth.py            # Run script for auth server
.env.example           # Environment variables template
README_LOGIN.md        # Quick reference
```

## Configuration

All configuration is via environment variables (see `.env.example`):

- `SECRET_KEY`: Flask secret key (required, 32+ bytes)
- `SQLALCHEMY_DATABASE_URI`: Database URI (default: `sqlite:///app.db`)
- `SESSION_COOKIE_SECURE`: Set to `true` for HTTPS (default: `true`)
- `AUTH_TOTP_ENABLED`: Enable/disable TOTP (default: `true`)
- `ARGON2_MEMORY`: Argon2 memory cost (default: 65536)
- `ARGON2_TIME`: Argon2 time cost (default: 3)
- `ARGON2_PARALLELISM`: Argon2 parallelism (default: 2)
- `RATE_PER_IP`: IP rate limit (default: `5 per minute`)
- `RATE_PER_USERNAME`: Username rate limit (default: `10 per 15 minutes`)
- `IDLE_TIMEOUT_MINUTES`: Session idle timeout (default: 15)
- `ABSOLUTE_TIMEOUT_HOURS`: Session absolute timeout (default: 8)

## Troubleshooting

**Import errors:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that Python version is 3.8+

**Database errors:**
- Ensure the database directory exists and is writable
- Check `SQLALCHEMY_DATABASE_URI` in `.env`

**2FA not working:**
- Verify system time is synchronized (TOTP requires accurate time)
- Check that the secret was scanned correctly
- Use the recovery secret if available

**Rate limiting too strict:**
- Adjust `RATE_PER_IP` and `RATE_PER_USERNAME` in `.env`
- Restart the server after changes

## Notes

- This is a **local-only** system (binds to 127.0.0.1)
- No email functionality (password reset must be done via CLI)
- Database uses SQLite by default (SQLAlchemy ORM)
- Logs are written to `logs/auth.log` with rotation
- Usernames are redacted in logs for security

