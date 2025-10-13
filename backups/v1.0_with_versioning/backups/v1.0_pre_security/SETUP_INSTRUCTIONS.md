# EU Trip Tracker - Setup & Running Instructions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- Flask (web framework)
- openpyxl (Excel import)
- argon2-cffi (password hashing)
- reportlab (PDF reports)
- pandas (data processing)

### 2. Initialize Database

The database will be created automatically on first run, but you can initialize it manually:

```bash
python app.py
```

This creates:
- `eu_tracker.db` (SQLite database)
- `settings.json` (configuration file)
- `logs/` directory (audit logs)
- `exports/` directory (DSAR exports)
- `compliance/` directory (data map)

### 3. Run the Application

```bash
python app.py
```

The application will start on: **http://127.0.0.1:5001**

### 4. Login

**Default credentials:**
- Password: `admin123`

⚠️ **IMPORTANT**: Change the password immediately after first login!

Go to **Admin → Settings → Change Password** or use the "Change Password" button in the sidebar.

---

## Configuration

All settings are stored in `settings.json` and can be modified via **Admin → Settings** or manually.

### Default Settings

```json
{
  "RETENTION_MONTHS": 36,
  "SESSION_IDLE_TIMEOUT_MINUTES": 30,
  "PASSWORD_HASH_SCHEME": "argon2",
  "DSAR_EXPORT_DIR": "./exports",
  "AUDIT_LOG_PATH": "./logs/audit.log",
  "SESSION_COOKIE_SECURE": false
}
```

### Configuration Options

#### RETENTION_MONTHS (default: 36)
How long to keep trip records after their exit date. Older trips will be deleted during retention purges.

#### SESSION_IDLE_TIMEOUT_MINUTES (default: 30)
Automatically log out after this many minutes of inactivity.

#### PASSWORD_HASH_SCHEME (default: "argon2")
Password hashing algorithm. Options: `argon2` (recommended) or `bcrypt`.

#### DSAR_EXPORT_DIR (default: "./exports")
Directory where DSAR export ZIP files are saved.

#### AUDIT_LOG_PATH (default: "./logs/audit.log")
Path to the audit log file.

#### SESSION_COOKIE_SECURE (default: false)
Enable secure cookies for HTTPS. Set to `true` in production with HTTPS.

---

## Usage

### Adding Employees

1. Navigate to **Dashboard**
2. Click **Add Employee** button
3. Enter employee name
4. Click **Add**

### Adding Trips

**Single Trip:**
1. Click on employee name from dashboard
2. Scroll to "Add Trip" section
3. Fill in: Country, Entry Date, Exit Date
4. Click **Add Trip**

**Bulk Trip (Multiple Employees):**
1. Navigate to **Add Trips** from sidebar
2. Select employees (checkboxes)
3. Fill in trip details
4. Click **Add Trip to Selected**

**Import from Excel:**
1. Navigate to **Import Data** from sidebar
2. Upload Excel file (.xlsx or .xls)
3. Review preview
4. Confirm import

### Viewing Compliance Status

**Dashboard View:**
- **Green**: Safe (< 60 days used)
- **Yellow**: Warning (60-80 days used)
- **Red**: Over limit (> 80 days used)

**Employee Detail:**
- Click employee name to see full trip history
- View days used in last 180 days
- See days until safe (if over limit)

**Calendar View:**
- Visual timeline of trips
- Color-coded by compliance status
- Filter by employee

### Exporting Data

**CSV Export:**
- Dashboard → Export button (all employees)
- Employee Detail → Export button (single employee)

**PDF Reports:**
- Employee Detail → PDF button (individual report)
- Dashboard → Export All PDF (summary report)

---

## GDPR Features

### Privacy Tools

Navigate to **Admin → Privacy Tools** for:

#### Employee Search
Search for an employee to perform DSAR actions.

#### Export Data (DSAR)
Generate a ZIP file containing:
- `employee.json` (employee record)
- `trips.csv` (all trips)
- `processing-notes.txt` (GDPR information)

Click **Export Data (ZIP)** and download.

#### Rectify Name
Update employee name:
1. Search employee
2. Click **Rectify Name**
3. Enter new name
4. Confirm

#### Anonymize
Replace employee name with "Employee #XXXX":
1. Search employee
2. Click **Anonymize**
3. Confirm

#### Delete Employee
Permanently delete employee and all trips:
1. Search employee
2. Click **Delete Employee**
3. Confirm (irreversible!)

### Retention Policy

**View Expired Trips:**
- Shows count of trips past retention period
- Click to view list

**Run Purge:**
1. Click **Run Retention Purge Now**
2. Review preview (trips/employees affected)
3. Confirm

**Change Retention Period:**
- Navigate to **Admin → Settings**
- Update "Retention Period (months)"
- Save Settings

### Settings Management

Navigate to **Admin → Settings** to configure:

- **Data Retention**: Retention period in months
- **Session Security**: Timeout, secure cookies
- **Password Security**: Hashing scheme
- **Export & Audit**: Directory paths

Click **Save Settings** to apply.

### Privacy Policy

Public page at **http://127.0.0.1:5001/privacy** (no login required).

Contains:
- What data we store
- Why we store it
- How long we keep it
- Your GDPR rights
- How to request access/deletion

---

## Testing

### Run Unit Tests

```bash
python test_gdpr.py
```

Or with pytest:

```bash
pytest test_gdpr.py -v
```

**Tests cover:**
- Password hashing (argon2, bcrypt)
- Retention policy and purge
- DSAR exports (ZIP contents)
- Employee deletion and rectification
- CSV and PDF exports
- Data minimisation (schema validation)

---

## Backup & Restore

### Backup

**Files to back up:**
```
eu_tracker.db           # Main database
settings.json           # Configuration
exports/                # DSAR exports
logs/                   # Audit logs
compliance/             # Data map
```

**Backup command (example):**
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz eu_tracker.db settings.json exports/ logs/ compliance/
```

### Restore

```bash
tar -xzf backup_YYYYMMDD.tar.gz
```

Then restart the application.

---

## Troubleshooting

### "Login failed"
- Check you're using correct password
- Check for rate limiting (5 attempts per 10 minutes)
- Review `logs/audit.log` for failed login attempts

### "Session expired"
- Increase `SESSION_IDLE_TIMEOUT_MINUTES` in Settings
- Or just log in again

### "Database is locked"
- Only one process can write at a time (SQLite limitation)
- Ensure no other instance is running
- Check for stale connections

### "Import failed"
- Verify Excel file format (.xlsx or .xls)
- Check column headers (Name, Country, Entry Date, Exit Date)
- Review error messages

### "Export directory not found"
- Check `DSAR_EXPORT_DIR` in settings
- Ensure directory exists and is writable
- Create manually if needed: `mkdir exports`

### Audit log errors
- Check `AUDIT_LOG_PATH` in settings
- Ensure directory exists: `mkdir logs`
- Verify write permissions

---

## Security Best Practices

### 1. Change Default Password
Immediately after first login, change from `admin123` to a strong password (12+ characters, mixed case, numbers, symbols).

### 2. Enable Secure Cookies (HTTPS)
If running over HTTPS:
1. Go to **Admin → Settings**
2. Check "Use Secure Cookies"
3. Save Settings

### 3. Regular Backups
- Back up database daily or weekly
- Store backups securely (encrypted)
- Test restore procedure

### 4. Run Retention Purges
- Manually: **Admin → Privacy Tools → Run Purge**
- Or schedule with cron/Task Scheduler

### 5. Review Audit Logs
Periodically review `logs/audit.log` for:
- Suspicious login attempts
- Unexpected deletions or exports
- Settings changes

### 6. Keep Software Updated
- Update Python packages: `pip install --upgrade -r requirements.txt`
- Monitor for security advisories

### 7. Restrict Access
- Run on localhost (127.0.0.1) only
- Use firewall to block external access
- No port forwarding

---

## Production Deployment

### Option 1: Local Network (Recommended)

Run on a local server accessible only within your office network.

1. Update `app.run()` in `app.py`:
```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

2. Enable secure cookies:
```python
app.config.update(SESSION_COOKIE_SECURE=True)
```

3. Use a reverse proxy (nginx, Apache) with HTTPS

4. Set firewall rules to restrict access

### Option 2: Single-User Laptop

Keep default settings (localhost only).

Pros:
- Maximum security (no network access)
- Simple setup

Cons:
- Only accessible from one computer

### Do NOT Deploy to Public Cloud

This system is designed for **local-only** use. Do not deploy to public cloud services (AWS, Azure, GCP) as it violates the "local storage only" design principle.

---

## File Structure

```
eu-trip-tracker/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── settings.json                   # User settings (generated)
├── eu_tracker.db                   # SQLite database (generated)
├── requirements.txt                # Python dependencies
├── test_gdpr.py                    # Unit tests
├── COMPLIANCE.md                   # GDPR compliance guide
├── SETUP_INSTRUCTIONS.md           # This file
├── README.md                       # Project overview
│
├── app/
│   ├── __init__.py
│   └── services/
│       ├── hashing.py              # Password hashing
│       ├── audit.py                # Audit logging
│       ├── retention.py            # Retention & purge
│       ├── dsar.py                 # DSAR operations
│       └── exports.py              # CSV/PDF exports
│
├── compliance/
│   └── data_map.yaml               # Data processing map
│
├── templates/
│   ├── base.html                   # Base template
│   ├── login.html                  # Login page
│   ├── dashboard.html              # Main dashboard
│   ├── employee_detail.html        # Employee detail view
│   ├── privacy.html                # Public privacy policy
│   ├── admin_privacy_tools.html    # DSAR tools
│   ├── admin_settings.html         # Settings page
│   └── expired_trips.html          # Expired trips list
│
├── static/
│   ├── css/
│   │   ├── global.css
│   │   └── hubspot-style.css
│   └── js/
│       └── hubspot-style.js
│
├── logs/                           # Audit logs (generated)
│   └── audit.log
│
└── exports/                        # DSAR exports (generated)
    └── (ZIP files)
```

---

## Support & Resources

### Documentation
- **COMPLIANCE.md**: Full GDPR compliance guide
- **compliance/data_map.yaml**: Data processing details
- **/privacy**: Public privacy policy (in app)

### GDPR Resources
- Official GDPR site: https://gdpr.eu/
- ICO guidance (UK): https://ico.org.uk/for-organisations/
- EDPB: https://edpb.europa.eu/

### Python/Flask Resources
- Flask docs: https://flask.palletsprojects.com/
- SQLite docs: https://www.sqlite.org/docs.html

---

## License

Internal use only. Not for redistribution.

---

## Questions?

Review the **COMPLIANCE.md** file for detailed GDPR procedures and operational guidelines.
