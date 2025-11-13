# ComplyEur Gold RC v3.9.1 — Deployment Quick Reference

## Quick Start

### 1. Install Render CLI
```bash
curl -fsSL https://render.com/install.sh | bash
```

### 2. Authenticate
```bash
render login
```

### 3. Deploy (Automated)
```bash
./scripts/deploy_render.sh
```

### 4. Deploy (Manual)
```bash
# Create service
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

# Set SECRET_KEY (REQUIRED)
render env:set complyeur-gold-rc SECRET_KEY "$(python3 -c 'import secrets; print(secrets.token_hex(32))')"

# Set other required variables
render env:set complyeur-gold-rc FLASK_ENV "production"
render env:set complyeur-gold-rc RENDER "true"
render env:set complyeur-gold-rc SESSION_COOKIE_SECURE "true"

# Enable HTTPS and auto-deploy
render services update complyeur-gold-rc --force-https true
render services update complyeur-gold-rc --auto-deploy true

# Trigger deployment
render deploy complyeur-gold-rc
```

## Verify Deployment

### Health Check
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

### Version Check
```bash
curl https://complyeur-gold-rc.onrender.com/api/version
```

## Monitor Deployment

### View Logs
```bash
render logs complyeur-gold-rc --tail
```

### Check Service Status
```bash
render services get complyeur-gold-rc
```

### View Environment Variables
```bash
render env:get complyeur-gold-rc
```

## Service Configuration

- **Service Name:** complyeur-gold-rc
- **Repository:** https://github.com/thisjamieguy/ComplyEur_Gold_RC_v3_9_1
- **Branch:** main
- **Region:** frankfurt
- **Health Check:** /health
- **Health Check Interval:** 30 seconds

## Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key (64-char hex) | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | Production environment | `production` |
| `RENDER` | Render platform flag | `true` |
| `SESSION_COOKIE_SECURE` | HTTPS session cookies | `true` |

## Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `DATABASE_PATH` | Database path | `/var/data/eu_tracker.db` |
| `PERSISTENT_DIR` | Persistent directory | `/var/data` |
| `AUDIT_LOG_PATH` | Audit log path | `logs/audit.log` |
| `EXPORT_DIR` | Export directory | `exports` |
| `BACKUP_DIR` | Backup directory | `/var/data/backups` |

## Health Check Endpoints

- `/health` - Main health check
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/healthz` - Alternative health check
- `/api/version` - API version

## Troubleshooting

### Deployment Fails
1. Check build logs in Render dashboard
2. Verify dependencies in `requirements.txt`
3. Check environment variables
4. Verify database initialization

### Health Check Fails
1. Check application logs
2. Verify database connection
3. Check environment variables
4. Verify health endpoint registration

### SSL/HTTPS Issues
1. Verify HTTPS enabled in dashboard
2. Check certificate provisioning
3. Verify force HTTPS setting

## Support

- **Documentation:** `docs/DEPLOYMENT_RENDER.md`
- **Deployment Script:** `scripts/deploy_render.sh`
- **Render Dashboard:** https://dashboard.render.com
- **Render Docs:** https://render.com/docs
