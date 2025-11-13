# ComplyEur Gold RC v3.9.1 — Render Dashboard Deployment Guide

## Quick Start: Deploy via Render Dashboard

### Step 1: Generate SECRET_KEY

**IMPORTANT:** Generate a secure SECRET_KEY first:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output - you'll need it in Step 5.

### Step 2: Go to Render Dashboard

1. Visit: https://dashboard.render.com
2. Sign in or create a free account
3. Click "New +" → "Web Service"

### Step 3: Connect GitHub Repository

1. Click "Connect account" if not already connected
2. Authorize Render to access your GitHub account
3. Select repository: `ComplyEur_Gold_RC_v3_9_1`
4. Select branch: `main`
5. Click "Connect"

### Step 4: Configure Service

Render will automatically detect `render.yaml` in your repository. Verify these settings:

#### Basic Settings
- **Name:** `complyeur-gold-rc`
- **Region:** `Frankfurt` (or your preferred region)
- **Branch:** `main`
- **Root Directory:** (leave empty)
- **Environment:** `Python 3`
- **Build Command:** `./scripts/render_build.sh`
- **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-file - --access-logfile -`
- **Plan:** `Starter` ($7/month)

#### Advanced Settings
- **Health Check Path:** `/health`
- **Health Check Interval:** `30 seconds`
- **Auto-Deploy:** `Yes` (deploy on every push to main)
- **Force HTTPS:** `Yes` (redirect HTTP to HTTPS)

### Step 5: Add Environment Variables

Click "Add Environment Variable" and add each variable:

#### Required Variables

1. **SECRET_KEY** (REQUIRED)
   - Key: `SECRET_KEY`
   - Value: (paste the SECRET_KEY you generated in Step 1)
   - Example: `b08bd0cb49d542e77ef100f9ab2b75803177788338f1002f54a758d7cec58e8f`

2. **FLASK_ENV**
   - Key: `FLASK_ENV`
   - Value: `production`

3. **RENDER**
   - Key: `RENDER`
   - Value: `true`

4. **SESSION_COOKIE_SECURE**
   - Key: `SESSION_COOKIE_SECURE`
   - Value: `true`

#### Database Variables (Optional - defaults in render.yaml)

5. **DATABASE_PATH**
   - Key: `DATABASE_PATH`
   - Value: `/var/data/eu_tracker.db`

6. **PERSISTENT_DIR**
   - Key: `PERSISTENT_DIR`
   - Value: `/var/data`

7. **BACKUP_DIR**
   - Key: `BACKUP_DIR`
   - Value: `/var/data/backups`

#### Logging Variables (Optional - defaults in render.yaml)

8. **LOG_LEVEL**
   - Key: `LOG_LEVEL`
   - Value: `INFO`

9. **AUDIT_LOG_PATH**
   - Key: `AUDIT_LOG_PATH`
   - Value: `logs/audit.log`

#### Export Variables (Optional - defaults in render.yaml)

10. **EXPORT_DIR**
    - Key: `EXPORT_DIR`
    - Value: `exports`

### Step 6: Add Persistent Disk

1. Scroll down to "Disks" section
2. Click "Add Disk"
3. Configure:
   - **Name:** `data`
   - **Mount Path:** `/var/data`
   - **Size:** `1 GB`
4. Click "Add"

**Why?** This ensures your database persists across deployments.

### Step 7: Review Configuration

Verify all settings:
- ✅ Service name: `complyeur-gold-rc`
- ✅ Region: `Frankfurt`
- ✅ Branch: `main`
- ✅ Build command: `./scripts/render_build.sh`
- ✅ Start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-file - --access-logfile -`
- ✅ Health check: `/health`
- ✅ Auto-deploy: `Yes`
- ✅ Force HTTPS: `Yes`
- ✅ SECRET_KEY: (set)
- ✅ Persistent disk: `data` (1 GB)

### Step 8: Create Service

1. Click "Create Web Service"
2. Render will start building your application
3. Monitor the build logs in real-time
4. Wait for deployment to complete (usually 3-5 minutes)

### Step 9: Verify Deployment

Once deployment completes:

1. **Check Service Status**
   - Status should be "Live"
   - Service URL: `https://complyeur-gold-rc.onrender.com`

2. **Test Health Endpoint**
   ```bash
   curl https://complyeur-gold-rc.onrender.com/health
   ```
   
   Expected response:
   ```json
   {
     "status": "ok",
     "uptime_seconds": 123,
     "version": "3.9.1",
     "env": "production"
   }
   ```

3. **Test Version Endpoint**
   ```bash
   curl https://complyeur-gold-rc.onrender.com/api/version
   ```
   
   Expected response:
   ```json
   {
     "version": "3.9.1"
   }
   ```

### Step 10: Post-Deployment Configuration

#### Enable Auto-Restart

1. Go to service settings
2. Scroll to "Auto-Restart"
3. Enable "Auto-restart on failure"
4. Save changes

#### Monitor Logs

1. Go to service dashboard
2. Click "Logs" tab
3. Monitor application logs in real-time

#### Set Up Monitoring (Optional)

1. Go to service settings
2. Enable "Health Checks" (should be enabled by default)
3. Set health check path: `/health`
4. Set health check interval: `30 seconds`

## Troubleshooting

### Build Fails

**Issue:** Build fails with dependency errors
**Solution:**
1. Check build logs for specific error
2. Verify `requirements.txt` is complete
3. Check Python version (should be 3.11.9)

**Issue:** Build fails with asset build errors
**Solution:**
1. Check if `scripts/build_assets.sh` is executable
2. Verify CSS/JS files exist in `app/static/`
3. Build script handles missing npm tools gracefully, so this should not be an issue

### Deployment Fails

**Issue:** Service fails to start
**Solution:**
1. Check application logs
2. Verify `SECRET_KEY` is set correctly
3. Verify database path is correct (`/var/data/eu_tracker.db`)
4. Check if persistent disk is mounted correctly

### Health Check Fails

**Issue:** Health endpoint returns 404 or 500
**Solution:**
1. Check application logs
2. Verify health endpoint is registered correctly
3. Check if database initialization is successful
4. Verify environment variables are set correctly

### SSL/HTTPS Issues

**Issue:** HTTPS not working
**Solution:**
1. Verify "Force HTTPS" is enabled in settings
2. Check certificate provisioning in logs
3. Wait a few minutes for SSL certificate to be issued

## Service URL

After successful deployment:
- **Service URL:** `https://complyeur-gold-rc.onrender.com`
- **Health Check:** `https://complyeur-gold-rc.onrender.com/health`
- **Version Check:** `https://complyeur-gold-rc.onrender.com/api/version`

## Environment Variables Summary

| Variable | Value | Required |
|----------|-------|----------|
| `SECRET_KEY` | (64-char hex) | ✅ Yes |
| `FLASK_ENV` | `production` | ✅ Yes |
| `RENDER` | `true` | ✅ Yes |
| `SESSION_COOKIE_SECURE` | `true` | ✅ Yes |
| `DATABASE_PATH` | `/var/data/eu_tracker.db` | No |
| `PERSISTENT_DIR` | `/var/data` | No |
| `LOG_LEVEL` | `INFO` | No |
| `AUDIT_LOG_PATH` | `logs/audit.log` | No |
| `EXPORT_DIR` | `exports` | No |
| `BACKUP_DIR` | `/var/data/backups` | No |

## Next Steps

1. ✅ **Deploy Service** - Follow steps above
2. ✅ **Verify Health Endpoint** - Test `/health` endpoint
3. ✅ **Enable Auto-Restart** - Configure in settings
4. ✅ **Monitor Logs** - Watch application logs
5. ✅ **Test Application** - Verify all features work
6. ✅ **Set Up Monitoring** - Configure alerts (optional)

## Support

- **Documentation:** `docs/DEPLOYMENT_RENDER.md`
- **Deployment Script:** `scripts/deploy_render.sh`
- **Render Dashboard:** https://dashboard.render.com
- **Render Documentation:** https://render.com/docs

---

**Ready to Deploy?** Follow the steps above to deploy ComplyEur Gold RC v3.9.1 to Render!
