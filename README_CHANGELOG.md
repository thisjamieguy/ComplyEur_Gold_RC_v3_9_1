# README_CHANGELOG

## v1.6.4 – QA Validation Ready

- Added a Python Playwright QA harness (`tests/qa_calendar_validation.py`) that seeds canonical data, validates rendering, accessibility, responsiveness, and performs regression smoke checks on core endpoints.
- Hardened calendar status colours (`safe` → `#15803d`, `warning` → `#c2410c`) so tooltip text and trip bars meet WCAG 2.1 AA contrast guidelines while preserving the existing compliance thresholds.
- Documented visual regression expectations and QA reporting workflow (`tests/visual/`, `docs/reports/QA_Phase3.5.3.md`) to support cross-discipline sign-off.
- Bumped the footer/application version to `v1.6.4` and refreshed automated tests to target the new asset revisions.

### Recommended Verification

```bash
# Run Flask in one terminal
python3 run_local.py

# In a second terminal validate the QA flow
python3 -m pytest tests/qa_calendar_validation.py
```

## v1.6.3 – Native Calendar Rendering & Validation

- Finalised the native JavaScript calendar renderer with cached `/api/trips` payloads, six-month navigation, and smooth scroll performance for large datasets.
- Replaced the placeholder state with keyboard-accessible trip bars, enriched tooltips, and an animated “Today” marker that stays in sync on resize.
- Added a detail overlay with compliance messaging, trip metadata, and modal focus management triggered by bar clicks or keyboard activation.
- Locked compliance colours to ≤70 (safe), 71–89 (warning), and ≥90 (critical) rolling totals, including visual swatches and assistive labelling.
- Expanded automated coverage with updated Node unit tests, Flask route assertions for calendar endpoints, and a Playwright E2E scenario covering render, tooltip, modal, and navigation flows.

### Recommended Verification

```bash
npm test
python3 -m pytest tests/test_app.py -k calendar
# Start the dev server before running Playwright:
# flask run
npx playwright test tests/e2e/calendar-native.spec.ts
```
