# ComplyEur Deployment Checklist

**Version**: 3.9.1 (Gold Release Candidate)  
**Last Updated**: 2025-11-12

This checklist ensures a safe and successful deployment of ComplyEur to production.

---

## Pre-Deployment

### 1. Code Review

- [ ] All code changes reviewed and approved
- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Playwright tests passing (`npm run test:qa`)
- [ ] No linter errors
- [ ] Documentation updated

### 2. Version Verification

- [ ] `VERSION` file updated to 3.9.1
- [ ] `CHANGELOG.md` updated with release notes
- [ ] Git tags created (if applicable)

### 3. Security Audit

- [ ] Security audit completed (`docs/security_audit.md`)
- [ ] No hardcoded secrets in code
- [ ] Environment variables configured
- [ ] Dependencies audited (`pip check`, `npm audit`)

### 4. Database Backup

- [ ] Production database backed up
- [ ] Backup verified (integrity check)
- [ ] Backup stored in secure location
- [ ] Rollback plan documented

### 5. Environment Preparation

- [ ] Production environment variables set
- [ ] `SECRET_KEY` configured (64-character hex string)
- [ ] `DATABASE_PATH` configured
- [ ] `SESSION_COOKIE_SECURE=true` (for HTTPS)
- [ ] All required directories created

---

## Deployment Steps

### Step 1: Pull Latest Code

```bash
# On production server
cd /path/to/complyeur
git pull origin main
# or
git checkout v3.9.1
```

**Verification**:
- [ ] Code updated to correct version
- [ ] `VERSION` file shows 3.9.1

### Step 2: Activate Virtual Environment

```bash
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

**Verification**:
- [ ] Virtual environment activated
- [ ] Prompt shows `(venv)`

### Step 3: Install/Update Dependencies

```bash
pip install -r requirements.txt
npm install  # If using Playwright tests
```

**Verification**:
- [ ] All packages installed successfully
- [ ] No dependency conflicts (`pip check`)
- [ ] No vulnerabilities (`npm audit`)

### Step 4: Run Database Migrations

```bash
# Database will auto-migrate on first run
# Or manually:
python -c "from app import create_app; app = create_app(); app.app_context().push(); from app.models import init_db; init_db()"
```

**Verification**:
- [ ] Database schema up to date
- [ ] No migration errors
- [ ] Database integrity check passes (`PRAGMA integrity_check;`)

### Step 5: Restart Application

**For Gunicorn:**
```bash
# Stop current process
pkill -f gunicorn
# or
systemctl stop complyeur

# Start new process
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
# or
systemctl start complyeur
```

**For Development Server:**
```bash
python run_local.py
```

**Verification**:
- [ ] Application starts without errors
- [ ] No error messages in logs
- [ ] Process running (`ps aux | grep gunicorn`)

### Step 6: Run Smoke Tests

```bash
# Run smoke test
python tools/smoke_test.py

# Or manual verification:
curl http://localhost:5000/health
```

**Verification**:
- [ ] Health check endpoint returns 200
- [ ] Application accessible at configured URL
- [ ] Login page loads correctly
- [ ] No errors in browser console

### Step 7: Verify Compliance Logic

```bash
# Run compliance calculation tests
pytest tests/test_rolling90.py -v
```

**Verification**:
- [ ] All compliance tests passing
- [ ] 90/180-day calculations correct
- [ ] Calendar displays correctly
- [ ] Risk levels calculated correctly

---

## Post-Deployment

### 1. Functional Verification

- [ ] Login works with admin credentials
- [ ] Dashboard loads correctly
- [ ] Employee list displays
- [ ] Trip addition works
- [ ] Calendar view renders
- [ ] Export functions work (CSV, PDF)
- [ ] Excel import works

### 2. Performance Verification

- [ ] Page load times acceptable (<2 seconds)
- [ ] Database queries performant
- [ ] No memory leaks
- [ ] Response times normal

### 3. Security Verification

- [ ] HTTPS enabled (if applicable)
- [ ] Security headers present
- [ ] Rate limiting active
- [ ] Session timeout working
- [ ] Audit logging active

### 4. Monitoring

- [ ] Application logs monitored
- [ ] Error logs checked
- [ ] Performance metrics tracked
- [ ] Uptime monitoring active

---

## Rollback Procedure

If issues are detected:

1. **Stop Application**
   ```bash
   pkill -f gunicorn
   # or
   systemctl stop complyeur
   ```

2. **Restore Previous Version**
   ```bash
   git checkout <previous-version-tag>
   # or
   git revert <commit-hash>
   ```

3. **Restore Database** (if needed)
   ```bash
   # Restore from backup
   cp data/backups/complyeur_backup_YYYYMMDD.db data/complyeur.db
   ```

4. **Restart Application**
   ```bash
   gunicorn wsgi:app --bind 0.0.0.0:5000
   ```

5. **Verify Rollback**
   - [ ] Application starts successfully
   - [ ] All functionality working
   - [ ] No data loss

See `docs/operations/rollback_procedure.md` for detailed rollback steps.

---

## Deployment Verification Checklist

### Critical Functions

- [ ] Authentication works
- [ ] Employee CRUD operations work
- [ ] Trip CRUD operations work
- [ ] 90/180-day calculations correct
- [ ] Calendar displays correctly
- [ ] Export functions work
- [ ] Excel import works

### Security Functions

- [ ] Password hashing works
- [ ] Session management works
- [ ] Rate limiting active
- [ ] CSRF protection active
- [ ] Security headers present
- [ ] Audit logging active

### Data Integrity

- [ ] Database integrity check passes
- [ ] Foreign key constraints enforced
- [ ] Data retention policy active
- [ ] Backup system working

---

## Troubleshooting

### Common Issues

**Issue**: Application won't start
- Check logs: `logs/app.log`
- Verify environment variables
- Check database path permissions
- Verify Python version (3.9+)

**Issue**: Database errors
- Run integrity check: `PRAGMA integrity_check;`
- Verify database file permissions
- Check database path in config

**Issue**: Import errors
- Verify virtual environment activated
- Check all dependencies installed
- Verify Python path

**Issue**: Port already in use
- Kill existing process: `pkill -f gunicorn`
- Change port in configuration
- Check firewall settings

---

## Deployment Sign-Off

### Deployment Completed By

- **Name**: _________________________
- **Date**: _________________________
- **Time**: _________________________
- **Version**: 3.9.1

### Verification Completed By

- **Name**: _________________________
- **Date**: _________________________
- **All Checks**: ✅ Passed / ❌ Failed

### Issues Encountered

- [ ] No issues
- [ ] Issues documented below:

_________________________________________________
_________________________________________________
_________________________________________________

### Sign-Off

- **Deployed By**: _________________________
- **Verified By**: _________________________
- **Approved By**: _________________________

---

## Post-Deployment Tasks

### Immediate (Within 1 Hour)

- [ ] Monitor application logs
- [ ] Check error rates
- [ ] Verify user access
- [ ] Test critical functions

### Short-Term (Within 24 Hours)

- [ ] Review performance metrics
- [ ] Check user feedback
- [ ] Verify backup system
- [ ] Update deployment documentation

### Long-Term (Within 1 Week)

- [ ] Review security logs
- [ ] Analyze performance trends
- [ ] Plan next deployment
- [ ] Update runbooks

---

## Additional Resources

- `docs/operations/rollback_procedure.md` - Detailed rollback steps
- `docs/security_audit.md` - Security audit report
- `docs/schema_summary.md` - Database schema documentation
- `TESTING.md` - Testing documentation

---

**Deployment Complete!** ✅

For issues or questions, refer to:
- Application logs: `logs/app.log`
- Error logs: `logs/audit.log`
- Documentation: `docs/`

