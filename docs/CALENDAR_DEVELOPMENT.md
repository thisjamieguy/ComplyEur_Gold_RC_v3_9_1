# Calendar Feature - Development Guide

## Status: In Development

The calendar feature is currently in active development and is **not available in production**. It will remain hidden from production users until it's ready for release.

## Development Access

### Option 1: Environment Variable (Recommended)

Set the `CALENDAR_DEV_MODE` environment variable:

```bash
export CALENDAR_DEV_MODE=true
python run_local.py
```

Or add to your `.env` file:
```
CALENDAR_DEV_MODE=true
```

### Option 2: Config File

Edit `settings.json` in the project root:

```json
{
  "CALENDAR_DEV_MODE": true
}
```

### Option 3: Automatic (Local Development)

The calendar is automatically enabled when:
- Not running in production (no `FLASK_ENV=production`)
- Not running on Render (`RENDER` env var not set)
- Not using Render's external hostname

## Access Routes

Once enabled, access the calendar via:

- **Main Calendar**: `/calendar` - Full calendar view
- **Dev Route**: `/calendar_dev` - Redirects to main calendar (for easy access)
- **Legacy Route**: `/calendar_view` - Redirects to calendar if enabled

## React Frontend Development

The calendar frontend is built with React + TypeScript + Vite and lives in:

**Location**: `app/frontend/calendar/`

### Running Frontend Standalone

```bash
cd app/frontend/calendar
npm install
npm run dev
```

This starts a Vite dev server (typically `http://localhost:5173`) for frontend-only development.

### Building for Production

```bash
cd app/frontend/calendar
npm run build
```

This builds the React app and updates the Flask template automatically.

## API Endpoints

The calendar uses the following API endpoints (all under `/api`):

- `GET /api/employees` - List all employees
- `GET /api/trips` - Get trips (with optional date filtering)
- `GET /api/trips/<id>` - Get specific trip
- `POST /api/trips` - Create new trip
- `PATCH /api/trips/<id>` - Update trip
- `DELETE /api/trips/<id>` - Delete trip
- `GET /api/forecast/<employee_id>` - Get compliance forecast
- `GET /api/alerts` - Get active compliance alerts

All endpoints require admin authentication.

## Current Features

- ✅ Interactive calendar view with drag-and-drop
- ✅ Employee timeline visualization
- ✅ Compliance alerts panel
- ✅ Trip CRUD operations
- ✅ Forecast panel
- ✅ Search and filtering

## Production Deployment

**Before enabling in production:**

1. Set `CALENDAR_DEV_MODE: false` in config (or remove env var)
2. Ensure React frontend is built (`npm run build` in `app/frontend/calendar/`)
3. Test all API endpoints
4. Verify authentication requirements
5. Update navigation menu (currently commented out in `base.html`)

## Notes

- The calendar navigation link is currently hidden in `app/templates/base.html`
- All calendar routes check `_is_calendar_enabled()` before allowing access
- Production users will see a "Calendar Unavailable" message if they try to access it
- The feature flag prevents accidental exposure in production

