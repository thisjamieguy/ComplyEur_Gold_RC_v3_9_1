# Quick Setup Guide - EU Trip Tracker v1.1

## 🚀 First-Time Setup (5 Minutes)

### 1. Install Dependencies
```bash
cd "/Users/jameswalsh/Desktop/iOS Dev/Web Projects/eu-trip-tracker"
pip install -r requirements.txt
```

### 2. Create .env File
```bash
# Copy the template
cp env_template.txt .env

# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Edit .env File
```bash
nano .env
```

Paste your generated secret key and set your admin password:
```
SECRET_KEY=<paste-your-64-char-hex-here>
ADMIN_PASSWORD=YourSecurePassword123
SESSION_COOKIE_SECURE=False
FLASK_DEBUG=False
FLASK_ENV=production
```

Save and exit (Ctrl+X, Y, Enter).

### 4. Run the Application
```bash
python app.py
```

### 5. First Login
1. Open browser: `http://127.0.0.1:5001`
2. Login with password from `.env`
3. **IMMEDIATELY** go to Settings → Change Admin Password
4. Use a strong password (8+ chars, letters + numbers)

---

## 🔐 Security Checklist

Before deployment to management:
- [ ] `.env` file created with unique SECRET_KEY
- [ ] Admin password changed from default
- [ ] Debug mode is `False` in .env
- [ ] Session timeout tested (30 minutes)
- [ ] GDPR notice visible in footer
- [ ] Exports download locally (no auto-upload)

---

## 📋 Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | *required* | Flask session encryption key |
| `ADMIN_PASSWORD` | `admin123` | Initial admin password (change!) |
| `FLASK_DEBUG` | `False` | Debug mode (NEVER True in production) |
| `SESSION_IDLE_TIMEOUT_MINUTES` | `30` | Auto-logout after inactivity |
| `SESSION_COOKIE_SECURE` | `False` | Set to `True` for HTTPS |
| `RETENTION_MONTHS` | `36` | Data retention period |

---

## 🛡️ Security Features

✅ **Password:** Argon2 hashing with salt  
✅ **Sessions:** 30-min timeout, secure cookies  
✅ **Input:** Full validation & sanitization  
✅ **GDPR:** Data deletion, privacy notices  
✅ **Exports:** Local only, no external upload  

---

## 📞 Troubleshooting

**Problem:** "No SECRET_KEY found in .env file!"  
**Solution:** Create `.env` file from `env_template.txt` and add generated key

**Problem:** Can't login  
**Solution:** Check `ADMIN_PASSWORD` in `.env` file matches what you're typing

**Problem:** Session keeps expiring  
**Solution:** Increase `SESSION_IDLE_TIMEOUT_MINUTES` in `.env`

**Problem:** Want to delete all data  
**Solution:** Admin Settings → Danger Zone → Type "DELETE ALL DATA"

---

## 📦 Backup Information

Current version backed up at:  
`/backups/v1.1_post_security/`

Original version available at:  
`/backups/v1.0_pre_security/`

---

**Version:** 1.1 (post-security review)  
**Status:** ✅ Production Ready  
**Last Updated:** October 8, 2025

