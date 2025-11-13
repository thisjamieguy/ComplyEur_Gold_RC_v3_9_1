# ComplyEur Gold RC v3.9.1 — Render Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying ComplyEur Gold RC v3.9.1 to Render.com with automated CI/CD from GitHub.

## Prerequisites

1. **GitHub Repository**: Repository must be pushed to GitHub
   - Repository URL: `https://github.com/thisjamieguy/ComplyEur_Gold_RC_v3_9_1`
   - Branch: `main`

2. **Render CLI**: Install Render CLI for automated deployment
   ```bash
   curl -fsSL https://render.com/install.sh | bash
   ```

3. **Environment Variables**: Prepare environment variables (see below)

4. **Render Account**: Sign up at [render.com](https://render.com) if needed

## Quick Deployment

### Automated Deployment Script

Use the provided deployment script for automated deployment:

```bash
./scripts/deploy_render.sh
```

This script will:
1. Validate repository structure
2. Check Render CLI installation
3. Authenticate with Render
4. Run pre-deployment checks
5. Create or update Render service
6. Set environment variables
7. Enable HTTPS and auto-deploy
8. Trigger deployment
9. Verify deployment
10. Generate deployment report

### Manual Deployment Steps

If you prefer manual deployment, follow these steps:

#### Step 1: Validate Repository

```bash
git fetch --all --tags
git status
grep -R "ComplyEur" render.yaml || echo "✅ Branding confirmed"
```

#### Step 2: Authenticate with Render CLI

```bash
render login
```

Follow the prompt to authenticate with your Render account.

#### Step 3: Create Render Service

```bash
render services create \
  --name "complyeur-gold-rc" \
  --repo "https://github.com/thisjamieguy/ComplyEur_Gold_RC_v3_9_1" \
  --branch main \
  --region frankfurt \
  --type web \
  --env python \
  --build-command "./scripts/render_build.sh" \
  --start-command "gunicorn wsgi:app --bind 0.0.0.0:\$PORT --log-file - --access-logfile -" \
  --plan starter
```

#### Step 4: Set Environment Variables

Set required environment variables in Render dashboard or via CLI:

**Required Variables:**
- `SECRET_KEY`: Generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `FLASK_ENV`: `production`
- `RENDER`: `true`
- `SESSION_COOKIE_SECURE`: `true`

**Database Variables:**
- `DATABASE_PATH`: `/var/data/eu_tracker.db`
- `PERSISTENT_DIR`: `/var/data`

**Optional Variables:**
- `LOG_LEVEL`: `INFO`
- `AUDIT_LOG_PATH`: `logs/audit.log`
- `EXPORT_DIR`: `exports`
- `BACKUP_DIR`: `/var/data/backups`

**Via CLI:**
```bash
render env:set complyeur-gold-rc SECRET_KEY "your-secret-key-here"
render env:set complyeur-gold-rc FLASK_ENV "production"
render env:set complyeur-gold-rc RENDER "true"
render env:set complyeur-gold-rc SESSION_COOKIE_SECURE "true"
```

#### Step 5: Enable HTTPS and Auto-Deploy

```bash
render services update complyeur-gold-rc --force-https true
render services update complyeur-gold-rc --auto-deploy true
```

#### Step 6: Run Pre-Deployment Validation

```bash
./scripts/check_security.py
./scripts/network_scan.sh
./scripts/run_phase1_full_tests.sh
```

#### Step 7: Trigger Deployment

```bash
render deploy complyeur-gold-rc
```

Or push to the `main` branch (if auto-deploy is enabled).

#### Step 8: Verify Deployment

Check health endpoint:

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

## Configuration Files

### render.yaml

The `render.yaml` file contains the service configuration:

```yaml
services:
  - type: web
    name: complyeur-gold-rc
    env: python
    region: frankfurt
    plan: starter
    branch: main
    buildCommand: ./scripts/render_build.sh
    startCommand: gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-file - --access-logfile -
    autoDeploy: true
    healthCheckPath: /health
    healthCheckIntervalSeconds: 30
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: FLASK_ENV
        value: production
      - key: RENDER
        value: "true"
      - key: DATABASE_PATH
        value: /var/data/eu_tracker.db
      - key: LOG_LEVEL
        value: INFO
      - key: PERSISTENT_DIR
        value: /var/data
      - key: SESSION_COOKIE_SECURE
        value: "true"
      - key: SECRET_KEY
        sync: false
    disks:
      - name: data
        mountPath: /var/data
        sizeGB: 1
```

### Environment Variables Template

Create a `.env` file locally with these variables (do not commit to git):

```bash
# Security - REQUIRED
SECRET_KEY=your-secret-key-here-change-this-to-a-random-64-character-hex-string

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
RENDER=true

# Database Configuration
DATABASE_PATH=/var/data/eu_tracker.db
PERSISTENT_DIR=/var/data

# Session Security
SESSION_COOKIE_SECURE=true
SESSION_IDLE_TIMEOUT_MINUTES=30

# Logging
LOG_LEVEL=INFO
AUDIT_LOG_PATH=logs/audit.log

# Export and Backup Directories
EXPORT_DIR=exports
BACKUP_DIR=/var/data/backups

# GDPR Compliance
RETENTION_MONTHS=36
DSAR_EXPORT_DIR=./exports
```

## Health Check Endpoints

The application provides multiple health check endpoints:

- `/health` - Main health check endpoint
- `/health/live` - Liveness probe (Kubernetes-style)
- `/health/ready` - Readiness probe (Kubernetes-style)
- `/healthz` - Alternative health check endpoint
- `/api/version` - API version endpoint

All endpoints return JSON with status, uptime, version, and environment.

## Post-Deployment Verification

### 1. Health Check

```bash
curl https://complyeur-gold-rc.onrender.com/health
```

### 2. Version Check

```bash
curl https://complyeur-gold-rc.onrender.com/api/version
```

### 3. Monitor Logs

```bash
render logs complyeur-gold-rc --tail
```

### 4. Check Service Status

```bash
render services get complyeur-gold-rc
```

## Troubleshooting

### Deployment Fails

1. **Check Build Logs**: View build logs in Render dashboard
2. **Verify Dependencies**: Ensure `requirements.txt` is complete
3. **Check Environment Variables**: Verify all required variables are set
4. **Database Initialization**: Check if database initialization is successful

### Health Check Fails

1. **Check Application Logs**: View application logs in Render dashboard
2. **Verify Database Connection**: Ensure database path is correct
3. **Check Environment Variables**: Verify `SECRET_KEY` and other variables
4. **Verify Health Endpoint**: Check if health endpoint is registered correctly

### SSL/HTTPS Issues

1. **Verify HTTPS Enabled**: Check Render dashboard settings
2. **Check Certificate**: Render automatically provisions SSL certificates
3. **Verify Force HTTPS**: Ensure force HTTPS is enabled in service settings

## Production Monitoring

### Enable Health Checks

1. Go to Render dashboard
2. Select your service
3. Navigate to Settings
4. Enable Health Checks
5. Set Health Check Path: `/health`
6. Set Health Check Interval: `30` seconds

### Enable Auto-Restarts

1. Go to Render dashboard
2. Select your service
3. Navigate to Settings
4. Enable Auto-restart on failure

### Cloudflare WAF (Optional)

If using Cloudflare, enable WAF rules:

1. Configure Cloudflare DNS
2. Enable WAF in Cloudflare dashboard
3. Apply rules from `infra/cloudflare/waf-rules.json`

## Security Checklist

- [ ] `SECRET_KEY` is set and secure (64-character hex string)
- [ ] `SESSION_COOKIE_SECURE` is set to `true`
- [ ] `FLASK_DEBUG` is set to `False`
- [ ] `FLASK_ENV` is set to `production`
- [ ] HTTPS is enabled and forced
- [ ] Database is stored on persistent disk
- [ ] Audit logging is enabled
- [ ] Health checks are configured
- [ ] Auto-restart is enabled
- [ ] Environment variables are secure (not in git)

## Maintenance

### Update Application

1. Make changes to code
2. Commit and push to `main` branch
3. Render will automatically deploy (if auto-deploy is enabled)
4. Monitor deployment in Render dashboard

### Update Environment Variables

```bash
render env:set complyeur-gold-rc VARIABLE_NAME "value"
```

### View Logs

```bash
render logs complyeur-gold-rc --tail
```

### Restart Service

```bash
render services restart complyeur-gold-rc
```

## Support

For issues or questions:
1. Check Render dashboard logs
2. Review deployment report in `/reports/deployment/`
3. Check application logs in Render dashboard
4. Verify environment variables in Render dashboard

## References

- [Render Documentation](https://render.com/docs)
- [Render CLI Documentation](https://render.com/docs/cli)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/latest/deploying/)
- [ComplyEur Documentation](./README.md)
