# ComplyEur Calendar Sandbox

This folder isolates the ComplyEur calendar so you can iterate on the UI and API without touching the main production application.

## Structure

- `calendar_app.py` – Minimal Flask entry point running only the calendar stack on port `5050`.
- `templates/` – Calendar Jinja templates (`calendar.html`, `timeline.html`, and reusable partials).
- `static/` – Standalone JavaScript, CSS, and assets required by the calendar.

## Running the Sandbox

From the project root:

```bash
cd "calendar_dev"
python calendar_app.py
```

The sandbox serves the calendar at `http://localhost:5050/`. Use `?employee_id=123` to focus a specific employee if they exist in the shared SQLite database.

## Notes

- The app reads from `data/eu_tracker.db` by default. Override with `CALENDAR_DEV_DB=/path/to/db` if needed.
- Admin session checks are satisfied automatically in this sandbox, so mutation endpoints remain usable.
- The blueprint in the main ComplyEur app is temporarily disabled to prevent route conflicts. All calendar changes should happen here until reintegration.

## Reintegration Checklist

1. Copy the updated assets back into the main application (`app/templates`, `app/static`).
2. Re-enable the calendar blueprint and routes in the main factory and router.
3. Optionally wrap the calendar API in a blueprint for cleaner registration (recommended).
4. Run the standard ComplyEur regression tests (`./tools/run_calendar_qa.sh`) before release.

### Example Calendar Route Snippet

```python
@app.route('/calendar')
def calendar():
    return render_template('calendar.html')
```

### Blueprint Reintegration (Optional but Recommended)

```python
# Copy-Ready Block
from flask import Blueprint, render_template

calendar_bp = Blueprint("calendar", __name__, url_prefix="/calendar")

@calendar_bp.route("/")
def calendar():
    return render_template("calendar.html")

app.register_blueprint(calendar_bp)
```

Document any additional changes in `CHANGELOG_v1.7.x.md` once reintegrated.

