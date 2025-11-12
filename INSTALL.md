# ComplyEur Installation Guide

**Version**: 3.9.1 (Gold Release Candidate)  
**Last Updated**: 2025-11-12

This guide provides step-by-step instructions for setting up ComplyEur on your local machine.

---

## Prerequisites

### Required Software

1. **Python 3.9 or higher**
   - Check your version: `python3 --version` or `python --version`
   - Download from [python.org](https://www.python.org/downloads/) if needed

2. **pip** (Python package manager)
   - Usually included with Python
   - Verify: `pip3 --version` or `pip --version`

3. **Node.js and npm** (for frontend tests)
   - Optional but recommended for running Playwright tests
   - Download from [nodejs.org](https://nodejs.org/)

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Disk Space**: ~200 MB (with virtual environment)
- **Memory**: 50-80 MB runtime
- **Network**: Not required after initial setup (local-only application)

---

## Step-by-Step Installation

### 1. Clone or Extract the Repository

```bash
# If using Git
git clone <repository-url>
cd ComplyEur

# Or extract the ZIP file to your desired location
```

### 2. Navigate to Project Directory

```bash
cd "ComplyEur v1.0.0 Post MVP"
```

### 3. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- Flask (web framework)
- SQLAlchemy (database ORM)
- Argon2 (password hashing)
- Playwright (testing)
- And other dependencies

**Note**: Installation may take 2-5 minutes depending on your internet connection.

### 5. Install Node.js Dependencies (Optional)

If you plan to run Playwright tests:

```bash
npm install
```

### 6. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example template
cp .env.example .env
```

Edit `.env` and configure:

```env
# Required: Generate a secure random key
SECRET_KEY=your-secret-key-here-change-this-to-a-random-64-character-hex-string

# Database path (default: data/complyeur.db)
DATABASE_PATH=data/complyeur.db

# Session settings
SESSION_COOKIE_SECURE=false  # Set to true for HTTPS
SESSION_IDLE_TIMEOUT_MINUTES=30

# Data retention (months)
RETENTION_MONTHS=36

# Export directory
EXPORT_DIR=./exports

# Audit log path
AUDIT_LOG_PATH=./logs/audit.log
```

**Important**: Replace `SECRET_KEY` with a secure random string. Generate one using:

```python
import secrets
print(secrets.token_hex(32))
```

### 7. Initialize the Database

The database will be created automatically on first run. To manually initialize:

```bash
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import init_db; init_db()"
```

### 8. Run the Application

**Development mode:**
```bash
python run_local.py
```

**Or using Flask directly:**
```bash
export FLASK_APP=run_local.py
flask run
```

The application will start at `http://localhost:5000`

### 9. First Login

1. Open your browser to `http://localhost:5000`
2. You'll be prompted to set up an admin account
3. Enter a secure password (minimum 8 characters)
4. Complete the setup form with your details

**Default credentials** (if database was pre-initialized):
- Username: `admin`
- Password: `admin123` (change immediately!)

---

## Verification

### Check Installation

1. **Verify Python packages:**
   ```bash
   pip list | grep -i flask
   ```

2. **Verify database:**
   ```bash
   # Check if database file exists
   ls -la data/complyeur.db
   ```

3. **Run smoke test:**
   ```bash
   python tools/smoke_test.py
   ```

### Test the Application

1. Navigate to `http://localhost:5000`
2. Log in with your admin credentials
3. Add a test employee
4. Add a test trip
5. Verify the calendar displays correctly

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'flask'`
- **Solution**: Activate your virtual environment and run `pip install -r requirements.txt`

**Issue**: `Port 5000 already in use`
- **Solution**: Change the port in `run_local.py` or kill the process using port 5000

**Issue**: `Database locked`
- **Solution**: Close any other instances of the application or database connections

**Issue**: `Permission denied` on database file
- **Solution**: Check file permissions: `chmod 644 data/complyeur.db`

**Issue**: Import errors
- **Solution**: Ensure you're in the project root directory and virtual environment is activated

### Getting Help

1. Check the logs in `logs/app.log`
2. Review the README.md for common solutions
3. Check the documentation in `/docs`
4. Review error messages in the browser console (F12)

---

## Next Steps

After installation:

1. **Change default password** (if applicable)
2. **Review settings** in Admin → Settings
3. **Add your first employee**
4. **Import existing trip data** (if you have Excel files)
5. **Review GDPR compliance settings**
6. **Set up automated backups** (if desired)

---

## Production Deployment

For production deployment on Render, Heroku, or similar platforms:

1. See `docs/operations/deployment_checklist.md`
2. Configure environment variables in your hosting platform
3. Set `SESSION_COOKIE_SECURE=true` for HTTPS
4. Configure database backups
5. Review security settings

---

## Uninstallation

To remove ComplyEur:

1. Deactivate virtual environment: `deactivate`
2. Delete the project directory
3. Remove database files (if desired): `rm -rf data/*.db`
4. Remove exports and backups (if desired)

**Note**: Uninstallation does not automatically delete your data. Manually remove the `data/` directory if you want to delete all stored information.

---

**Installation Complete!** 🎉

For more information, see:
- `README.md` - Overview and features
- `TESTING.md` - Running tests
- `docs/` - Additional documentation

