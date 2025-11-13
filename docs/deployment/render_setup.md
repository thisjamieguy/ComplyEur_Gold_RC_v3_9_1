# Render Deployment Configuration – ComplyEur Gold RC v3.9.1

**Version**: 3.9.1 (Gold Release Candidate)  
**Date**: 2025-11-12  
**Status**: Production-Ready

## Overview

This document provides step-by-step instructions for deploying ComplyEur to Render. Render is a modern cloud platform that simplifies deployment of web applications with automatic SSL, scaling, and monitoring.

---

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: ComplyEur_Gold_RC_v3_9_1 must be pushed to GitHub
3. **Environment Variables**: Prepare secure values for `SECRET_KEY` and other variables

---

## Deployment Configuration

### Basic Settings

- **Name**: `complyeur-gold-rc`
- **Environment**: `Python 3.11`
- **Region**: `Frankfurt (EU)` (for GDPR compliance)
- **Branch**: `main`
- **Root Directory**: `/` (root of repository)
- **Auto Deploy**: `Yes` (enables automatic deployments on push to main)

### Build Command

```bash
./scripts/render_build.sh
```

### Start Command

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

**Alternative** (if using `run_local.py`):

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### Health Check Path

```
/health
```

---

## Environment Variables

Configure the following environment variables in Render Dashboard:

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key (generate secure random string) | `your-secret-key-here` |
| `DATABASE_URL` | Database connection string | `sqlite:///complyeur.db` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Flask application entry point | `app:app` |
| `PYTHON_VERSION` | Python version | `3.11` |
| `PORT` | Server port (auto-set by Render) | `8000` |

### Generating SECRET_KEY

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or use OpenSSL:

```bash
openssl rand -hex 32
```

---

## Step-by-Step Deployment Instructions

### 1. Log into Render

1. Navigate to [render.com](https://render.com)
2. Sign in or create an account
3. Verify your account (if required)

### 2. Create New Web Service

1. Click **"New +"** in the Render Dashboard
2. Select **"Web Service"**
3. Click **"Connect GitHub"** (if not already connected)
4. Authorize Render to access your GitHub repositories

### 3. Connect Repository

1. Search for **"ComplyEur_Gold_RC_v3_9_1"** in the repository list
2. Select the repository
3. Click **"Connect"**

### 4. Configure Service Settings

1. **Name**: Enter `complyeur-gold-rc`
2. **Region**: Select **"Frankfurt (EU)"**
3. **Branch**: Select **"main"**
4. **Root Directory**: Leave empty (uses root)
5. **Runtime**: Select **"Python 3"**
6. **Build Command**: Enter `./scripts/render_build.sh`
7. **Start Command**: Enter `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 5. Configure Environment Variables

1. Scroll down to **"Environment Variables"** section
2. Click **"Add Environment Variable"**
3. Add each variable:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = `<your-generated-secret-key>`
   - `DATABASE_URL` = `sqlite:///complyeur.db`

### 6. Configure Advanced Settings

1. **Auto-Deploy**: Enable **"Yes"** (automatically deploys on push to main)
2. **Health Check Path**: Enter `/health`
3. **Plan**: Select appropriate plan (Free tier available for testing)

### 7. Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying your application
3. Monitor the build logs for any errors
4. Wait for deployment to complete (typically 2-5 minutes)

### 8. Verify Deployment

1. Once deployment completes, Render will provide a URL (e.g., `https://complyeur-gold-rc.onrender.com`)
2. Navigate to the URL in your browser
3. Verify the application loads correctly
4. Test the health endpoint: `https://your-app.onrender.com/health`

---

## Post-Deployment Configuration

### 1. Custom Domain (Optional)

1. Go to **Settings** → **Custom Domains**
2. Add your domain (e.g., `complyeur.com`)
3. Follow DNS configuration instructions
4. Render will automatically provision SSL certificate

### 2. Database Setup

For SQLite (default):
- Database file is stored in Render's filesystem
- **Note**: SQLite on Render's filesystem is ephemeral and will be lost on redeploy
- For production, consider using Render's PostgreSQL database

For PostgreSQL (recommended for production):
1. Create a new **PostgreSQL** database in Render
2. Update `DATABASE_URL` environment variable:
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```
3. Run database migrations (if applicable)

### 3. Monitoring and Logs

1. **Logs**: View application logs in Render Dashboard → **Logs** tab
2. **Metrics**: Monitor CPU, memory, and request metrics in **Metrics** tab
3. **Alerts**: Set up alerts for errors or performance issues

### 4. Backup Configuration

1. Configure automatic backups for database (if using PostgreSQL)
2. Set up regular backups of application data
3. Test backup and restore procedures

---

## Troubleshooting

### Build Failures

**Issue**: Build fails with dependency errors

**Solution**:
1. Check `requirements.txt` for correct package versions
2. Verify Python version compatibility
3. Check build logs for specific error messages
4. Ensure all dependencies are listed in `requirements.txt`

### Runtime Errors

**Issue**: Application crashes on startup

**Solution**:
1. Check application logs in Render Dashboard
2. Verify environment variables are set correctly
3. Ensure `SECRET_KEY` is set and valid
4. Check database connection string (if using external database)
5. Verify `gunicorn` is installed and configured correctly

### Database Issues

**Issue**: Database connection errors

**Solution**:
1. Verify `DATABASE_URL` is correct
2. Check database credentials
3. Ensure database is accessible from Render's network
4. For SQLite, verify file permissions and path

### Health Check Failures

**Issue**: Health check endpoint returns errors

**Solution**:
1. Verify `/health` route exists in application
2. Check health check path in Render settings
3. Ensure application is listening on correct port
4. Check application logs for errors

---

## Security Considerations

### 1. Environment Variables

- **Never** commit sensitive values to repository
- Use Render's environment variable encryption
- Rotate `SECRET_KEY` regularly
- Use strong, randomly generated secrets

### 2. Database Security

- Use strong database passwords
- Enable SSL/TLS for database connections
- Restrict database access to Render's IP addresses
- Regularly backup database

### 3. Application Security

- Enable HTTPS (automatic with Render)
- Use secure session cookies
- Implement rate limiting
- Regularly update dependencies

### 4. GDPR Compliance

- Store data in EU region (Frankfurt)
- Implement data retention policies
- Enable DSAR (Data Subject Access Request) tools
- Regular security audits

---

## Scaling Configuration

### Horizontal Scaling

1. Go to **Settings** → **Scaling**
2. Configure auto-scaling based on traffic
3. Set minimum and maximum instance counts
4. Configure scaling thresholds

### Vertical Scaling

1. Upgrade Render plan for more resources
2. Monitor CPU and memory usage
3. Optimize application performance
4. Consider database scaling if using PostgreSQL

---

## Rollback Procedure

### Manual Rollback

1. Go to **Deployments** tab in Render Dashboard
2. Find previous successful deployment
3. Click **"Rollback"** button
4. Confirm rollback
5. Verify application functionality

### Automated Rollback

1. Configure health check monitoring
2. Set up automatic rollback on health check failures
3. Monitor deployment metrics
4. Test rollback procedure regularly

---

## Maintenance

### Regular Updates

1. Monitor dependency updates (Dependabot)
2. Test updates in staging environment
3. Deploy updates during low-traffic periods
4. Monitor application after deployment

### Backup Strategy

1. Regular database backups (daily)
2. Application configuration backups
3. Test backup restoration procedures
4. Store backups in secure location

### Monitoring

1. Set up application monitoring (e.g., Sentry)
2. Configure log aggregation
3. Set up alerting for errors
4. Monitor performance metrics

---

## Support and Resources

### Render Documentation

- [Render Documentation](https://render.com/docs)
- [Python Deployment Guide](https://render.com/docs/deploy-python)
- [Environment Variables](https://render.com/docs/environment-variables)

### ComplyEur Documentation

- [README.md](../../README.md)
- [INSTALL.md](../../INSTALL.md)
- [TESTING.md](../../TESTING.md)
- [Deployment Checklist](../operations/deployment_checklist.md)
- [Rollback Procedure](../operations/rollback_procedure.md)

---

## Success Criteria

✅ Application deploys successfully  
✅ Health check endpoint responds  
✅ Application is accessible via URL  
✅ Environment variables are configured  
✅ Database is accessible (if using external database)  
✅ SSL certificate is provisioned  
✅ Monitoring is configured  
✅ Backups are set up  

---

## Next Steps

1. **Test Deployment**: Verify all functionality works correctly
2. **Configure Domain**: Set up custom domain (if applicable)
3. **Enable Monitoring**: Set up application monitoring and alerts
4. **Configure Backups**: Set up regular database backups
5. **Documentation**: Update internal documentation with deployment URL
6. **Team Access**: Grant team members access to Render Dashboard
7. **Security Audit**: Conduct security audit of deployed application

---

**Last Updated**: 2025-11-12  
**Version**: 3.9.1 (Gold Release Candidate)  
**Status**: Production-Ready
