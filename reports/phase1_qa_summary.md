# Phase 1 QA Summary

## Fixes & Verification
- **Tripline tooltips** – Added projected days-remaining metadata with higher z-index tooltip (manual hover check + Playwright scenario planned; blocked by host Chromium permission).
- **Employee trip history** – Server now calculates per-trip rolling usage/remaining; regression covered by `pytest tests/test_rolling90.py` and manual inspection.
- **Dashboard forecast column** – Dashboard shows next-job forecasted days remaining using backend forecasts (verified manually after API edits).
- **Cache invalidation** – Calendar mutations now invalidate dashboard cache automatically (manual regression via trip edits).

## Automated Tests
| Suite | Command | Result | Notes |
| --- | --- | --- | --- |
| Unit | `python3 -m pytest tests/test_rolling90.py` | ✅ Pass | Confirms rolling window + Schengen detection updates |
| Playwright | `npx playwright test tests/phase1_core_logic.spec.js --config=playwright.config.js` | ⚠️ Blocked | macOS sandbox denied Chromium headless launch (`bootstrap_check_in ... Permission denied`) |

The Playwright suite contains the four required scenarios (each looped 3×) but execution is blocked in this environment. See `reports/phase1_test_report.json` for metadata.
