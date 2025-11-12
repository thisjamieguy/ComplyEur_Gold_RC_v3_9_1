# ComplyEur E2E Test Suite - Overnight QA Soak

## Overview

This comprehensive end-to-end test suite automates the full user journey: login → import Excel fixture → verify calculations → cross-check UI vs backend.

## Test File

**`tests/e2e/test_full_login_import.spec.ts`**

### What It Does

1. **Automatic Login**
   - Navigates to app URL
   - Fills password field (no username required)
   - Submits and waits for dashboard

2. **Excel Import**
   - Navigates to import page
   - Selects random fixture from `data/fixtures/`
   - Uploads file via file input
   - Waits for import completion

3. **Data Verification**
   - Extracts employee data from dashboard table
   - Gets days used, days remaining from UI
   - Fetches backend data via API or employee detail page
   - Compares values with 100% parity check

4. **Artifact Collection**
   - Screenshots at each stage
   - Diff JSON files for any mismatches
   - Comparison logs for audit trail

## Running the Test

### Standalone Test

```bash
# Set credentials (optional, defaults to admin/admin123)
export TEST_USER="admin"
export TEST_PASS="admin123"

# Run single test
npx playwright test tests/e2e/test_full_login_import.spec.ts

# With HTML report
npx playwright test tests/e2e/test_full_login_import.spec.ts --reporter=html
```

### Overnight Soak Test

```bash
# Activate virtual environment
source venv/bin/activate

# Set duration (default: 8 hours)
export HOURS=8

# Set credentials
export TEST_USER="admin"
export TEST_PASS="admin123"

# Run overnight soak
bash scripts/soak_run.sh
```

The soak script will:
- Generate fresh fixtures each iteration
- Run backend unit tests
- Execute the E2E test
- Loop continuously for specified hours
- Save all artifacts and reports

## Fixture Generation

**`scripts/make_fixtures.py`** generates both Excel (.xlsx) and CSV files:

```bash
python scripts/make_fixtures.py
```

Generates:
- `data/fixtures/fix_0.xlsx` through `fix_9.xlsx` (Excel format)
- `data/fixtures/fix_0.csv` through `fix_9.csv` (CSV backup)

Each fixture contains:
- 5 employees (Emp1 through Emp5)
- 20 trips per employee
- Random dates within a 300-day window
- Trip durations: 1-30 days

## Artifacts

### Screenshots
- `tests/artifacts/screenshots/1_login_success_*.png`
- `tests/artifacts/screenshots/2_import_page_*.png`
- `tests/artifacts/screenshots/3_import_complete_*.png`
- `tests/artifacts/screenshots/4_dashboard_verified_*.png`

### Diff Files
- `tests/artifacts/diffs/diff_*.json` - Mismatches detected
- `tests/artifacts/diffs/comparison_*.json` - All comparisons (audit)

### Reports
- `playwright-report/index.html` - HTML test report
- `tests/reports/pytest_report.html` - Backend test report

## Test Configuration

### Environment Variables

- `TEST_USER` - Admin username (default: "admin")
- `TEST_PASS` - Admin password (default: "admin123")
- `E2E_HOST` - App hostname (default: "127.0.0.1")
- `E2E_PORT` - App port (default: 5001)
- `HOURS` - Soak duration in hours (default: 8)

### Expected Behavior

- **Login**: 5-10 seconds
- **Import**: 5-15 seconds (depends on file size)
- **Verification**: 2-5 seconds
- **Total per iteration**: ~2-3 minutes

## Troubleshooting

### Test Fails at Login
- Verify app is running on `http://127.0.0.1:5001` (or set `E2E_HOST` and `E2E_PORT` env vars)
- Check password is correct (default: `admin123`)
- Ensure login page is accessible
- Verify Playwright storage state exists at `tests/auth/state.json` (run global setup if missing)

### Import Fails
- Verify fixtures exist: `ls data/fixtures/`
- Check file format (must be .xlsx or .xls)
- Ensure `openpyxl` is installed: `pip install openpyxl`

### Backend API Not Found
- Test uses fallback: extracts from employee detail page
- API endpoint `/api/trips/summary?employee=<id>` is optional
- Test will work with or without this endpoint

### No Mismatches but Test Fails
- Check browser console for JavaScript errors
- Verify dashboard is rendering correctly
- Check network tab for failed API calls

## Next Phase Enhancements

Future improvements planned:
- Visual regression testing (Playwright snapshots)
- Accessibility checks (axe-core integration)
- Memory/time budget metrics
- 24-hour continuous reliability mode
- Performance benchmarks per iteration

## Support

For issues or questions:
1. Check `tests/artifacts/diffs/` for mismatch details
2. Review screenshots in `tests/artifacts/screenshots/`
3. Check Playwright HTML report: `npx playwright show-report`


