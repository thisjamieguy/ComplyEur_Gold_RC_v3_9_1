# 🚀 Maavsi Calendar Diagnostics - Quick Start

## Backend Tests (Python/Flask)

```bash
# Run all diagnostic tests
python3 -m pytest -v tests/calendar_diagnostics.py

# Quick test with minimal output
python3 -m pytest tests/calendar_diagnostics.py -q

# Stop on first failure
python3 -m pytest tests/calendar_diagnostics.py --maxfail=1
```

**Expected Output:**
```
✅ /api/trips → 302 (authentication required)
✅ /api/employees → 302 (authentication required)  
✅ /calendar_view → 200
✅ Database connectivity: PASS
✅ Error handling: PASS
============================== 10 passed in 0.80s ==============================
```

## Frontend Tests (React/TypeScript)

```bash
# Navigate to frontend
cd app/frontend/calendar

# Run test commands
npm run test:diagnostics

# Open browser test runner
open src/tests/test-runner.html
```

**Expected Output:**
```
✅ CalendarShell Mounts: PASS
✅ TripLayer Renders: PASS  
✅ Component Props: PASS
✅ Error Boundaries: PASS
✅ API Integration: PASS
Overall Status: ✅ ALL TESTS PASSED
```

## 🎯 What Each Test Validates

### Backend Tests
- **API Endpoints**: Authentication, response codes, data structure
- **Database**: Connectivity, CRUD operations, data integrity
- **Error Handling**: Invalid requests, malformed data, edge cases
- **Security**: Authentication, CSRF, input validation

### Frontend Tests  
- **Component Mounting**: React components render without errors
- **API Integration**: Frontend can communicate with backend
- **Error Boundaries**: Graceful error handling
- **Props Handling**: Components accept data correctly

## 🔧 Troubleshooting

### Backend Issues
- **302 Redirects**: Normal for unauthenticated API calls
- **Import Errors**: Check virtual environment activation
- **Database Errors**: Verify file permissions on `data/eu_tracker.db`

### Frontend Issues
- **Test Runner**: Open `test-runner.html` in browser manually
- **API Calls**: Ensure Flask server is running on port 5000
- **Component Errors**: Check browser console for React errors

## 📊 Success Criteria

**✅ All Systems Go:**
- Backend: 10/10 tests passing
- Frontend: 5/5 tests passing  
- No 500 errors detected
- Authentication working
- Database operations stable

**❌ Issues Found:**
- Check `test_report.json` for details
- Review console output for specific failures
- Verify all dependencies installed

---

*Run diagnostics regularly during development to ensure system stability!*




