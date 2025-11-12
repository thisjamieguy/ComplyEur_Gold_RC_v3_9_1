# 🔐 Automated Login State Management for ComplyEur QA

This document explains the automated login state system that allows Playwright tests to run headless overnight without manual login intervention.

## Overview

The system automatically:
1. Saves login credentials in a `.env` file (local-only, git-ignored)
2. Generates a Playwright session state file (`tests/auth/state.json`) on first run
3. Reuses the saved session for all subsequent test runs
4. Regenerates the state if it's missing or expired

## Quick Start

### 1. First-Time Setup

The `.env` file is automatically created by `scripts/full_overnight_qa.sh` with default credentials:

```bash
TEST_USER=admin
TEST_PASS=admin123
APP_URL=http://localhost:5001
```

**⚠️ Important:** Edit `.env` if your credentials differ from the defaults.

### 2. Generate Login State

Run once to generate the login state:

```bash
npx tsx scripts/save_login_state.ts
```

This will:
- Open Chromium (visible)
- Log into ComplyEur
- Save session cookies to `tests/auth/state.json`
- Close the browser

### 3. Run Overnight QA

Start the full overnight QA suite:

```bash
source venv/bin/activate
bash scripts/full_overnight_qa.sh
```

The script will:
- ✅ Check for `.env` (create if missing)
- ✅ Check for `tests/auth/state.json` (generate if missing)
- ✅ Run all test suites using the saved login state

## Files Created

- `.env` - Test credentials (git-ignored, local only)
- `tests/auth/state.json` - Playwright session state (git-ignored)
- `scripts/save_login_state.ts` - Login state generator script

## How It Works

1. **Playwright Config** (`playwright.config.ts`):
   - Automatically detects if `tests/auth/state.json` exists
   - If present, injects it into all test contexts via `storageState`
   - Tests run with authenticated session, bypassing login

2. **Login State Generator** (`scripts/save_login_state.ts`):
   - Reads credentials from `.env`
   - Logs into ComplyEur via Playwright
   - Saves browser context state (cookies, localStorage, etc.)
   - Writes to `tests/auth/state.json`

3. **Overnight QA Script** (`scripts/full_overnight_qa.sh`):
   - Checks for login state before running tests
   - Regenerates state if missing
   - Runs all test suites headless

## Troubleshooting

### Login State Generation Fails

If `npx tsx scripts/save_login_state.ts` fails:

1. **Check app is running:**
   ```bash
   curl http://localhost:5001/healthz
   ```
   Or start the app:
   ```bash
   source venv/bin/activate
   python run_local.py
   ```

2. **Verify credentials:**
   ```bash
   cat .env
   ```

3. **Check login page:**
   ```bash
   open http://localhost:5001/login
   ```

### Tests Still Stuck at Login

1. **Verify state file exists:**
   ```bash
   ls -la tests/auth/state.json
   ```

2. **Regenerate state:**
   ```bash
   rm tests/auth/state.json
   npx tsx scripts/save_login_state.ts
   ```

3. **Check Playwright config:**
   ```bash
   grep -A 2 "storageState" playwright.config.ts
   ```

## Security Notes

- `.env` is git-ignored (never committed)
- `tests/auth/state.json` is git-ignored (contains session cookies)
- Default password `admin123` should be changed in production
- Session state expires naturally with the server session timeout

## Future Enhancements

- [ ] Automatic re-login if state expires mid-run
- [ ] State expiration detection and refresh
- [ ] Multiple environment support (dev/staging/prod)
- [ ] Visual regression snapshots with authenticated state
