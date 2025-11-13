# Health Check Settings in Render Dashboard

## Where to Find Health Check Interval

The **Health Check Interval** is **NOT** on the Auto-Deploy settings page (the page you're currently viewing). It's in a different section.

## Location in Render Dashboard

### Option 1: Service Settings (After Service is Created)

1. **Go to your service dashboard**
   - Navigate to: `https://dashboard.render.com`
   - Click on your service: `complyeur-gold-rc`

2. **Go to Settings**
   - Click "Settings" tab in the left sidebar
   - Scroll down to "Health Checks" section

3. **Health Check Settings**
   - **Health Check Path:** `/health` (should already be set from render.yaml)
   - **Health Check Interval:** `30 seconds` (should already be set from render.yaml)

### Option 2: During Service Creation

If you're creating the service for the first time:

1. **Scroll down past the Auto-Deploy section**
   - Look for "Health Checks" section
   - Or "Advanced Settings" section

2. **Health Check Configuration**
   - **Health Check Path:** `/health`
   - **Health Check Interval:** `30 seconds`

### Option 3: Automatic from render.yaml

**Good News:** Since your `render.yaml` already includes:

```yaml
healthCheckPath: /health
healthCheckIntervalSeconds: 30
```

Render will **automatically apply these settings** when you create the service from the repository. You don't need to set them manually if you're using `render.yaml`!

## Current Configuration (from render.yaml)

```yaml
healthCheckPath: /health
healthCheckIntervalSeconds: 30
```

This means:
- **Health Check Path:** `/health`
- **Health Check Interval:** `30 seconds` (Render checks every 30 seconds)

## How to Verify Health Check Settings

### After Service is Created:

1. **Go to Service Dashboard**
   - Navigate to your service: `complyeur-gold-rc`
   - Click "Settings" tab

2. **Check Health Checks Section**
   - Look for "Health Checks" section
   - Verify:
     - Health Check Path: `/health`
     - Health Check Interval: `30 seconds` (or similar)

3. **Test Health Check**
   - Click "Test Health Check" button (if available)
   - Or test manually:
     ```bash
     curl https://complyeur-gold-rc.onrender.com/health
     ```

## What You're Currently Viewing

The page you're seeing (Auto-Deploy settings) includes:
- ✅ **Pre-Deploy Command** - Commands to run before deployment
- ✅ **Auto-Deploy** - Automatic deployment settings
- ✅ **Build Filters** - Paths to include/ignore for builds

**This page does NOT include:**
- ❌ Health Check Interval
- ❌ Health Check Path
- ❌ Health Check Settings

## Next Steps

### If Using render.yaml (Recommended):

1. **Continue with service creation**
   - The health check settings will be applied automatically from `render.yaml`
   - You don't need to set them manually

2. **After service is created:**
   - Go to Settings → Health Checks
   - Verify the settings are applied correctly

### If Not Using render.yaml:

1. **Continue scrolling down** on the service creation page
2. **Look for "Health Checks" section**
3. **Set:**
   - Health Check Path: `/health`
   - Health Check Interval: `30 seconds`

## Summary

- **Current Page:** Auto-Deploy settings (does NOT have Health Check Interval)
- **Health Check Settings:** In a different section (Settings → Health Checks)
- **Your Configuration:** Already set in `render.yaml` (will be applied automatically)
- **Action Required:** None - settings will be applied automatically from `render.yaml`

## Verification After Deployment

After your service is deployed, verify the health check:

```bash
# Test health endpoint
curl https://complyeur-gold-rc.onrender.com/health

# Expected response:
# {
#   "status": "ok",
#   "uptime_seconds": 123,
#   "version": "3.9.1",
#   "env": "production"
# }
```

---

**Note:** Since your `render.yaml` already includes the health check configuration, Render will automatically apply these settings when you create the service. You can continue with the service creation process without manually setting the health check interval.




