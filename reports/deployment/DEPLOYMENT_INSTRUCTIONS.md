# ComplyEur Gold RC v3.9.1 — Deployment Instructions

## Deployment Method Options

Since Render CLI installation may vary by system, here are three deployment methods:

### Option 1: Render Dashboard (Recommended - Easiest)

The easiest way to deploy is through the Render dashboard:

1. **Go to Render Dashboard**
   - Visit: https://dashboard.render.com
   - Sign in or create an account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `https://github.com/thisjamieguy/ComplyEur_Gold_RC_v3_9_1`
   - Select branch: `main`

3. **Configure Service**
   - **Name:** `complyeur-gold-rc`
   - **Region:** `Frankfurt`
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Environment:** `Python 3`
   - **Build Command:** `./scripts/render_build.sh`
   - **Start Command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT --log-file - --access-logfile -`
   - **Plan:** `Starter`

4. **Add Environment Variables**
   Click "Add Environment Variable" and add:
   - `SECRET_KEY` = (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
   - `FLASK_ENV` = `production`
   - `RENDER` = `true`
   - `SESSION_COOKIE_SECURE` = `true`
   - `DATABASE_PATH` = `/var/data/eu_tracker.db`
   - `PERSISTENT_DIR` = `/var/data`
   - `LOG_LEVEL` = `INFO`
   - `AUDIT_LOG_PATH` = `logs/audit.log`
   - `EXPORT_DIR` = `exports`
   - `BACKUP_DIR` = `/var/data/backups`

5. **Add Persistent Disk**
   - Click "Add Disk"
   - **Name:** `data`
   - **Mount Path:** `/var/data`
   - **Size:** `1 GB`

6. **Configure Advanced Settings**
   - **Health Check Path:** `/health`
   - **Health Check Interval:** `30 seconds`
   - **Auto-Deploy:** `Yes`
   - **Force HTTPS:** `Yes`

7. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Monitor build logs

8. **Verify Deployment**
   ```bash
   curl https://complyeur-gold-rc.onrender.com/health
   ```

### Option 2: Render CLI (Command Line)

If you prefer using the CLI:

1. **Install Render CLI**
   ```bash
   # macOS (Homebrew)
   brew install render
   
   # Or via npm
   npm install -g render-cli
   
   # Or download binary from: https://github.com/renderinc/cli/releases
   ```

2. **Authenticate**
   ```bash
   render login
   ```

3. **Run Deployment Script**
   ```bash
   ./scripts/deploy_render.sh
   ```

   Or manually:
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
   python3 -c "import secrets; print(secrets.token_hex(32))"
   render env:set complyeur-gold-rc SECRET_KEY "your-generated-secret-key"
   
   # Set other variables
   render env:set complyeur-gold-rc FLASK_ENV "production"
   render env:set complyeur-gold-rc RENDER "true"
   render env:set complyeur-gold-rc SESSION_COOKIE_SECURE "true"
   
   # Enable HTTPS and auto-deploy
   render services update complyeur-gold-rc --force-https true
   render services update complyeur-gold-rc --auto-deploy true
   
   # Trigger deployment
   render deploy complyeur-gold-rc
   ```

### Option 3: GitHub Actions (CI/CD)

For automated deployments on every push:

1. **Create GitHub Actions Workflow**
   Create `.github/workflows/deploy.yml`:
   ```yaml
   name: Deploy to Render
   
   on:
     push:
       branches:
         - main
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - name: Checkout code
           uses: actions/checkout@v4
   
         - name: Deploy to Render
           uses: JorgeLNJunior/render-deploy@v1.4.6
           with:
             service_id: ${{ secrets.RENDER_SERVICE_ID }}
             api_key: ${{ secrets.RENDER_API_KEY }}
             clear_cache: true
             wait_deploy: true
             github_deployment: true
             deployment_environment: 'production'
             github_token: ${{ secrets.GITHUB_TOKEN }}
   ```

2. **Set GitHub Secrets**
   - Go to GitHub repository → Settings → Secrets → Actions
   - Add `RENDER_SERVICE_ID` (get from Render dashboard)
   - Add `RENDER_API_KEY` (get from Render dashboard → Account Settings → API Keys)

3. **Push to Main Branch**
   - Any push to `main` will trigger deployment

## Generate SECRET_KEY

**IMPORTANT:** You must generate a secure SECRET_KEY before deployment:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as the `SECRET_KEY` environment variable.

## Verify Deployment

After deployment, verify the health endpoint:

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

## Post-Deployment Configuration

### Enable Health Checks
1. Go to Render dashboard
2. Select service: `complyeur-gold-rc`
3. Navigate to Settings
4. Enable Health Checks
5. Set Health Check Path: `/health`
6. Set Health Check Interval: `30 seconds`

### Enable Auto-Restarts
1. Go to Render dashboard
2. Select service: `complyeur-gold-rc`
3. Navigate to Settings
4. Enable Auto-restart on failure

### Monitor Logs
```bash
# Via Dashboard
# Go to service → Logs tab

# Via CLI (if installed)
render logs complyeur-gold-rc --tail
```

## Troubleshooting

### Deployment Fails
1. Check build logs in Render dashboard
2. Verify `requirements.txt` is complete
3. Check environment variables are set correctly
4. Verify database initialization

### Health Check Fails
1. Check application logs in Render dashboard
2. Verify database connection
3. Check environment variables (especially `SECRET_KEY`)
4. Verify health endpoint is registered correctly

### SSL/HTTPS Issues
1. Verify HTTPS is enabled in dashboard
2. Check certificate provisioning
3. Verify force HTTPS setting

## Service URL

After deployment, your service will be available at:
- **URL:** `https://complyeur-gold-rc.onrender.com`
- **Health Check:** `https://complyeur-gold-rc.onrender.com/health`

## Support

- **Documentation:** `docs/DEPLOYMENT_RENDER.md`
- **Deployment Script:** `scripts/deploy_render.sh`
- **Render Dashboard:** https://dashboard.render.com
- **Render Documentation:** https://render.com/docs

---

**Recommended Method:** Option 1 (Render Dashboard) is the easiest and most reliable method for first-time deployment.




