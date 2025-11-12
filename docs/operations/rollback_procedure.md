# ComplyEur Rollback Procedure

**Version**: 3.9.1 (Gold Release Candidate)  
**Last Updated**: 2025-11-12

This document provides step-by-step instructions for rolling back ComplyEur to a previous version in case of deployment issues.

---

## When to Rollback

Rollback should be considered if:

- Critical functionality is broken
- Data integrity issues are detected
- Security vulnerabilities are discovered
- Performance degradation is severe
- User access is compromised

**Decision Criteria**: If the issue cannot be fixed within 15 minutes, proceed with rollback.

---

## Pre-Rollback Checklist

### 1. Document the Issue

- [ ] Issue description documented
- [ ] Error messages captured
- [ ] Screenshots taken (if applicable)
- [ ] Logs saved
- [ ] User impact assessed

### 2. Verify Backup Availability

- [ ] Database backup exists
- [ ] Backup is recent (<24 hours old)
- [ ] Backup integrity verified
- [ ] Previous code version identified

### 3. Notify Stakeholders

- [ ] Users notified of maintenance window
- [ ] Team notified of rollback
- [ ] Rollback window scheduled

---

## Rollback Steps

### Step 1: Stop the Application

**For Gunicorn:**
```bash
# Find the process
ps aux | grep gunicorn

# Stop gracefully
pkill -f gunicorn

# Or force kill if needed
kill -9 <PID>
```

**For Systemd:**
```bash
systemctl stop complyeur
```

**For Development Server:**
```bash
# Press Ctrl+C in the terminal
# Or kill the process
pkill -f "python run_local.py"
```

**Verification**:
- [ ] Application process stopped
- [ ] Port 5000 is free (`lsof -i :5000` or `netstat -an | grep 5000`)

### Step 2: Backup Current State

```bash
# Create rollback backup
cd /path/to/complyeur
cp data/complyeur.db data/complyeur_rollback_$(date +%Y%m%d_%H%M%S).db

# Backup current code
git tag rollback_$(date +%Y%m%d_%H%M%S)
```

**Verification**:
- [ ] Database backup created
- [ ] Backup file exists and is readable
- [ ] Git tag created

### Step 3: Restore Previous Code Version

**Option A: Git Tag (Recommended)**
```bash
cd /path/to/complyeur
git fetch --tags
git checkout <previous-version-tag>
# Example: git checkout v3.9.0
```

**Option B: Git Commit**
```bash
cd /path/to/complyeur
git log --oneline  # Find previous commit
git checkout <commit-hash>
# Example: git checkout abc1234
```

**Option C: Git Revert**
```bash
cd /path/to/complyeur
git revert <commit-hash>
```

**Verification**:
- [ ] Code reverted to previous version
- [ ] `VERSION` file shows previous version
- [ ] No uncommitted changes (`git status`)

### Step 4: Restore Database (If Needed)

**Only restore database if:**
- Schema changes were made
- Data corruption occurred
- Data loss is suspected

**Restore from Backup:**
```bash
# Stop application (already done in Step 1)

# Backup current database
cp data/complyeur.db data/complyeur_before_restore_$(date +%Y%m%d_%H%M%S).db

# Restore from backup
cp data/backups/complyeur_backup_YYYYMMDD.db data/complyeur.db

# Verify integrity
sqlite3 data/complyeur.db "PRAGMA integrity_check;"
# Should return: ok
```

**Verification**:
- [ ] Database restored
- [ ] Integrity check passes
- [ ] Database file permissions correct

### Step 5: Reinstall Dependencies (If Needed)

**Only if requirements.txt changed:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Verification**:
- [ ] All dependencies installed
- [ ] No dependency conflicts (`pip check`)

### Step 6: Restart Application

**For Gunicorn:**
```bash
source venv/bin/activate
gunicorn wsgi:app --bind 0.0.0.0:5000 --workers 4
```

**For Systemd:**
```bash
systemctl start complyeur
```

**For Development Server:**
```bash
source venv/bin/activate
python run_local.py
```

**Verification**:
- [ ] Application starts without errors
- [ ] No error messages in logs
- [ ] Process running

### Step 7: Verify Rollback

**Health Check:**
```bash
curl http://localhost:5000/health
# Should return: {"status": "ok"}
```

**Functional Tests:**
- [ ] Login works
- [ ] Dashboard loads
- [ ] Employee list displays
- [ ] Trip addition works
- [ ] Calendar displays
- [ ] Export functions work

**Database Verification:**
```bash
sqlite3 data/complyeur.db "SELECT COUNT(*) FROM employees;"
sqlite3 data/complyeur.db "SELECT COUNT(*) FROM trips;"
```

**Verification**:
- [ ] All critical functions working
- [ ] No data loss
- [ ] Performance acceptable

---

## Post-Rollback Tasks

### 1. Document Rollback

- [ ] Rollback reason documented
- [ ] Rollback steps recorded
- [ ] Issues encountered documented
- [ ] Timeline recorded

### 2. Notify Stakeholders

- [ ] Users notified of completion
- [ ] Team notified of status
- [ ] Rollback summary shared

### 3. Investigate Root Cause

- [ ] Root cause analysis started
- [ ] Fix identified (if applicable)
- [ ] Prevention measures planned

### 4. Plan Re-Deployment

- [ ] Issues fixed (if applicable)
- [ ] Re-deployment plan created
- [ ] Testing completed
- [ ] Re-deployment scheduled

---

## Rollback Scenarios

### Scenario 1: Code Issue (No Database Changes)

**Steps**:
1. Stop application
2. Restore previous code version
3. Restart application
4. Verify functionality

**Database**: No action needed

### Scenario 2: Database Schema Issue

**Steps**:
1. Stop application
2. Restore previous code version
3. Restore database from backup
4. Restart application
5. Verify functionality

**Database**: Restore from backup

### Scenario 3: Data Corruption

**Steps**:
1. Stop application
2. Restore database from backup
3. Verify data integrity
4. Restart application
5. Verify functionality

**Code**: No action needed (if code is fine)

### Scenario 4: Complete Rollback

**Steps**:
1. Stop application
2. Restore previous code version
3. Restore database from backup
4. Reinstall dependencies (if needed)
5. Restart application
6. Verify functionality

**Both**: Code and database restored

---

## Rollback Verification Checklist

### Application Status

- [ ] Application running
- [ ] No error messages
- [ ] Health check passes
- [ ] Logs clean

### Functionality

- [ ] Login works
- [ ] Dashboard loads
- [ ] Employee CRUD works
- [ ] Trip CRUD works
- [ ] Calendar displays
- [ ] Export functions work
- [ ] Excel import works

### Data Integrity

- [ ] Database integrity check passes
- [ ] Employee count correct
- [ ] Trip count correct
- [ ] No data loss
- [ ] Foreign keys intact

### Performance

- [ ] Page load times acceptable
- [ ] Database queries performant
- [ ] No memory leaks
- [ ] Response times normal

---

## Emergency Contacts

**Development Team**: [Contact Information]  
**DevOps Team**: [Contact Information]  
**On-Call Engineer**: [Contact Information]

---

## Rollback Sign-Off

### Rollback Completed By

- **Name**: _________________________
- **Date**: _________________________
- **Time**: _________________________
- **Previous Version**: _________________________

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

- **Rolled Back By**: _________________________
- **Verified By**: _________________________
- **Approved By**: _________________________

---

## Additional Resources

- `docs/operations/deployment_checklist.md` - Deployment procedures
- `docs/security_audit.md` - Security audit report
- `docs/schema_summary.md` - Database schema documentation
- Application logs: `logs/app.log`
- Error logs: `logs/audit.log`

---

**Rollback Complete!** ✅

For questions or issues, refer to:
- Application logs: `logs/app.log`
- Error logs: `logs/audit.log`
- Documentation: `docs/`

