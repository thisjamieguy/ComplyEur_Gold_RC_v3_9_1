# Phase 3.7 Test Suite — Run Instructions

## Quick Start

### Step 1: Start the Flask Application

Open a terminal and run:

```bash
# Option 1: Using the run script
bash scripts/run_app.sh

# Option 2: Direct Python
python run_auth.py

# Option 3: Using run_local.py (if you don't need auth)
python run_local.py
```

The app should start on `http://127.0.0.1:5001`

### Step 2: Run the Test File

In a **new terminal window**, run:

```bash
# Run just this test file
npx playwright test tests/phase3_7_intense_validation.spec.js

# Or run with UI mode (interactive)
npx playwright test tests/phase3_7_intense_validation.spec.js --ui

# Or run in headed mode (see the browser)
npx playwright test tests/phase3_7_intense_validation.spec.js --headed
```

## Detailed Options

### Run All Tests
```bash
npm run test:qa
# or
npx playwright test
```

### Run Specific Test
```bash
# By test name
npx playwright test -g "fullscreen toggle"

# By file
npx playwright test tests/phase3_7_intense_validation.spec.js
```

### Debug Mode
```bash
# Step through tests with debugger
npx playwright test tests/phase3_7_intense_validation.spec.js --debug

# Or use the inspector
PWDEBUG=1 npx playwright test tests/phase3_7_intense_validation.spec.js
```

### View Test Results
```bash
# HTML report (opens automatically)
npx playwright show-report

# Or view screenshots
open tests/artifacts/screenshots/
```

## Environment Variables

You can customize the test settings:

```bash
# Different port
E2E_PORT=5002 npx playwright test tests/phase3_7_intense_validation.spec.js

# Different host
E2E_HOST=localhost npx playwright test tests/phase3_7_intense_validation.spec.js

# Custom admin password
ADMIN_PASS=yourpassword npx playwright test tests/phase3_7_intense_validation.spec.js

# Full custom URL
PLAYWRIGHT_BASE_URL=http://localhost:8080 npx playwright test tests/phase3_7_intense_validation.spec.js
```

## Troubleshooting

### Port Already in Use
If port 5001 is busy, either:
- Stop the other process using that port
- Use a different port: `E2E_PORT=5002 npx playwright test ...`

### Authentication Fails
The test uses default password `admin123`. If your app uses a different password:
```bash
ADMIN_PASS=yourpassword npx playwright test tests/phase3_7_intense_validation.spec.js
```

### Tests Fail with "Element Not Found"
- Make sure the Flask app is running
- Check that you have trip data in the database
- Verify the calendar page loads correctly in your browser

### View Screenshots
Screenshots are saved to:
```
tests/artifacts/screenshots/
```

## What the Tests Do

1. **Fullscreen Toggle** — Tests fullscreen mode activation/deactivation
2. **Context Menu** — Verifies right-click menu appears with options
3. **Drag-Drop** — Tests trip dragging and API persistence
4. **Hover/Tooltips** — Checks trip details on hover
5. **API Validation** — Tests PATCH endpoint for trip updates
6. **Performance** — Measures drag operation timing

All tests include screenshots for visual regression testing.

