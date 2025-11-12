# Secure Login (Local) - Quick Reference

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set SECRET_KEY (use: python3 -c "import secrets; print(secrets.token_hex(32))")
   ```

3. **Create first admin:**
   ```bash
   export FLASK_APP=run_auth.py
   flask admin create --username admin
   ```

4. **Run server:**
   ```bash
   python run_auth.py
   ```
   Access at `http://127.0.0.1:5001/login`

## Features

- **Argon2id** password hashing (configurable)
- **TOTP 2FA** (enabled by default)
- **Session timeouts** (15 min idle, 8h absolute)
- **Rate limiting** (5/min per IP, 10/15min per username)
- **Account lockout** (exponential backoff after 5 failures)
- **CSRF protection** (Flask-WTF)
- **Security headers** (CSP, HSTS, no-sniff, etc.)
- **Secure logging** (username redaction)

## CLI Commands

```bash
flask admin create --username <name>          # Create admin user
flask admin reset-password --username <name>  # Reset password
flask admin enable-2fa --username <name>     # Enable 2FA
flask admin disable-2fa --username <name>    # Disable 2FA
```

## 2FA Setup

1. Login with username/password
2. Visit `/setup-2fa`
3. Scan QR code with authenticator app
4. Save the secret key securely
5. Enter code on next login

For detailed documentation, see `INSTALLATION_AUTH.md`

