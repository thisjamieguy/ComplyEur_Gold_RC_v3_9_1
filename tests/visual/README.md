# Visual Baselines — Native Calendar

This folder stores the canonical screenshots used for visual regression checks against the native JavaScript calendar (Phase 3.5 build).

Baseline files expected by the QA workflow:

- `tests/visual/baseline_calendar_desktop.png`
- `tests/visual/baseline_calendar_tablet.png`
- `tests/visual/baseline_calendar_mobile.png`

To refresh these captures:

1. Start the Flask application locally (`FLASK_APP=wsgi.py flask run` or `python3 run_local.py`).
2. Launch Playwright (Python or TypeScript) and sign in with the default admin credentials.
3. Navigate to `/calendar`, ensure the QA seed data is present, and call `page.screenshot(path=...)` for each viewport (1440×900, 820×900, 414×896).
4. Verify the images before committing them as updated baselines.

Keep this directory in sync with the latest production-ready visuals so automated diffs can reliably flag unintended UI changes.
