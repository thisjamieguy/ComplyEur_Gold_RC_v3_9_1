# ComplyEur Playwright UI Test Suite

## 🎯 What This Test Suite Does

This comprehensive UI validation suite automatically:
- **Crawls every page** in the ComplyEur application
- **Clicks all buttons, links, and interactive elements**
- **Tests all forms** with safe dummy data
- **Detects 500 errors** and server issues
- **Captures console errors** and JavaScript exceptions
- **Validates redirects** and authentication flows
- **Screenshots failures** for debugging
- **Re-runs tests** until all pass

## 📁 Structure

```
qa/playwright/
├── tests/
│   └── full-site-crawl.spec.js      # Main test suite (9 comprehensive tests)
├── utils/
│   ├── crawler.js                   # Recursive site crawler
│   └── formTester.js                # Automated form testing
├── reports/                         # JSON and HTML test reports
├── screenshots/                     # Failure screenshots and page captures
├── playwright.config.js             # Playwright configuration
├── run_full_ui_validation.sh        # Master test runner script
└── README.md                        # This file
```

## 🚀 Quick Start

### Run All Tests

```bash
cd "/Users/jameswalsh/Desktop/Dev/Web Projects/ComplyEur/ComplyEur v1.0.0 Post MVP"
./qa/playwright/run_full_ui_validation.sh
```

This will:
1. Start Flask automatically
2. Run all 9 test suites
3. Generate HTML and JSON reports
4. Capture screenshots on failure
5. Retry failed tests up to 3 times

### Run Specific Tests

```bash
cd qa/playwright
npx playwright test tests/full-site-crawl.spec.js
```

### Run in Headed Mode (See Browser)

```bash
cd qa/playwright
npx playwright test --headed
```

### View HTML Report

```bash
cd qa/playwright
npx playwright show-report reports/playwright-report
```

## 📋 Test Coverage

### 1. **Public Pages Crawl**
- Discovers all public pages (landing, privacy, help, etc.)
- Validates status codes
- Checks for broken links
- Monitors console errors

### 2. **Login Testing**
- Tests invalid credentials
- Tests successful login
- Validates redirect to dashboard
- Checks error messages

### 3. **Authenticated Pages Crawl**
- Logs in as admin
- Crawls all protected pages
- Tests dashboard, calendar, admin pages
- Validates permissions

### 4. **Form Testing**
- Finds all forms on dashboard
- Fills fields with appropriate dummy data
- Validates form submissions
- Captures before/after screenshots

### 5. **Employee Management**
- Tests add employee flow
- Validates employee table rendering
- Checks for UI elements

### 6. **Trip Management**
- Tests bulk add trip page
- Tests Excel import page
- Tests what-if scenario calculator
- Tests future job alerts

### 7. **Calendar Functionality**
- Tests calendar page loading
- Validates calendar UI elements
- Checks for JavaScript errors
- Tests drag-and-drop (if available)

### 8. **Admin Pages**
- Tests admin settings
- Tests privacy tools
- Tests retention management
- Validates access control

### 9. **JavaScript Error Detection**
- Monitors console for JS errors
- Tests key pages for exceptions
- Validates clean execution

## 📊 Test Results

### Reports Generated

1. **HTML Report**: `reports/playwright-report/index.html`
   - Visual test results
   - Screenshots on failure
   - Detailed timing information

2. **JSON Reports**:
   - `reports/public-crawl-results.json` - Public pages crawl data
   - `reports/authenticated-crawl-results.json` - Protected pages data
   - `reports/test-results.json` - Overall test results

3. **Screenshots**: `screenshots/*.png`
   - Captured on failure
   - Page states during testing
   - Form filling snapshots

### Reading Results

```bash
# View HTML report in browser
open qa/playwright/reports/playwright-report/index.html

# Check JSON results
cat qa/playwright/reports/authenticated-crawl-results.json | jq .

# View screenshots
open qa/playwright/screenshots/
```

## 🔧 Configuration

### Playwright Config (`playwright.config.js`)

Key settings:
- **Timeout**: 30 seconds per test
- **Retries**: 2 automatic retries on failure
- **Workers**: 1 (sequential testing to avoid conflicts)
- **Screenshots**: Captured on failure
- **Video**: Recorded on failure

### Test Runner Script (`run_full_ui_validation.sh`)

Features:
- Auto-starts Flask server
- Waits for server to be ready
- Runs tests with retry logic
- Analyzes results automatically
- Cleans up processes on exit

## 🐛 Troubleshooting

### Tests Failing?

1. **Check Flask is running**:
   ```bash
   curl http://localhost:5001/health
   ```

2. **View detailed errors**:
   ```bash
   cat qa/playwright/reports/test-output.log
   ```

3. **Check screenshots**:
   ```bash
   ls -lah qa/playwright/screenshots/
   ```

4. **Run in headed mode to watch**:
   ```bash
   cd qa/playwright
   npx playwright test --headed
   ```

### Common Issues

**Port 5001 already in use**:
```bash
pkill -f "python3 run_local.py"
sleep 2
python3 run_local.py &
```

**Playwright not installed**:
```bash
cd qa/playwright
npm install --save-dev @playwright/test
npx playwright install chromium
```

**Tests timing out**:
- Increase timeout in `playwright.config.js`
- Check Flask logs: `tail -f logs/app.log`

## 📈 Continuous Integration

### GitHub Actions Example

```yaml
name: UI Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - uses: actions/setup-python@v4
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          cd qa/playwright && npm install
      - name: Run tests
        run: ./qa/playwright/run_full_ui_validation.sh
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: qa/playwright/reports/
```

## 🎨 Customizing Tests

### Add New Test

Create a new file in `tests/`:

```javascript
const { test, expect } = require('@playwright/test');

test('my custom test', async ({ page }) => {
  await page.goto('http://localhost:5001/my-page');
  expect(await page.title()).toBe('My Page');
});
```

### Modify Crawler

Edit `utils/crawler.js` to:
- Change max depth: `maxDepth: 5`
- Add URL filters
- Customize link extraction

### Modify Form Tester

Edit `utils/formTester.js` to:
- Add custom dummy data
- Skip certain forms
- Add validation rules

## 📝 Best Practices

1. **Run tests before deployment**
2. **Review screenshots on failure**
3. **Keep tests in sync with UI changes**
4. **Use descriptive test names**
5. **Monitor console errors**
6. **Test on clean database state**

## 🔗 Useful Commands

```bash
# Run all tests
./qa/playwright/run_full_ui_validation.sh

# Run specific test file
npx playwright test tests/full-site-crawl.spec.js

# Run specific test by name
npx playwright test -g "should test login"

# Debug mode (pause on failure)
npx playwright test --debug

# Generate new report
npx playwright show-report

# Update snapshots
npx playwright test --update-snapshots

# Run with specific browser
npx playwright test --project=chromium
```

## 📞 Support

For issues or questions:
1. Check the HTML report for detailed errors
2. Review screenshots in `screenshots/`
3. Check Flask logs in `logs/app.log`
4. Review test output in `reports/test-output.log`

## ✅ Success Criteria

Tests pass when:
- ✅ All routes return 200 or valid redirects
- ✅ No 500 server errors
- ✅ No JavaScript console errors
- ✅ All forms can be filled and submitted
- ✅ All pages render without exceptions
- ✅ Authentication flows work correctly
- ✅ Calendar functionality loads properly

---

**Last Updated**: 2025-11-13  
**Version**: 1.0.0  
**Status**: ✅ Fully Operational

