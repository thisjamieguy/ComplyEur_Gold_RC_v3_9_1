# Test Overview Page - Removal Instructions

## Purpose
This temporary test page verifies that Excel imports and 90/180-day calculations are working correctly.

## Access
Visit: `http://localhost:5000/test-overview` (or your configured host/port)

You can also access it via the **🧪 Test Overview** link in the sidebar (highlighted in yellow).

## Features
- ✅ Shows all employees with their travel compliance data
- 📊 Displays days used, days remaining, and status (🟢 Safe / 🟠 Warning / 🔴 Exceeded)
- 🔄 "Reload Excel Data" button to reimport from the latest Excel file
- 📝 Summary line showing total employees, trips, and last import time
- ⚠️ Ireland trips are automatically excluded from 90-day calculations

## How to Remove (When Testing is Complete)

### Step 1: Delete the test route file
```bash
rm test_overview.py
```

### Step 2: Remove the blueprint registration from app.py
Open `app.py` and delete these lines (around line 33-40):
```python
# ================================================================================
# TEMPORARY TEST ROUTE - REMOVE WHEN TESTING COMPLETE
# ================================================================================
# Import and register test overview blueprint
# TO REMOVE: Delete these 3 lines and delete test_overview.py file
from test_overview import test_bp
app.register_blueprint(test_bp)
# ================================================================================
```

### Step 3: Remove the sidebar link from base.html
Open `templates/base.html` and delete these lines (around line 84-92):
```html
<!-- TEMPORARY TEST LINK - REMOVE WHEN TESTING COMPLETE -->
<a href="{{ url_for('test_overview.test_overview') }}" class="nav-item ...">
    <svg class="nav-icon" ...>...</svg>
    <span>🧪 Test Overview</span>
</a>
<!-- END TEMPORARY TEST LINK -->
```

### Step 4: Delete the template file
```bash
rm templates/test_overview.html
```

### Step 5: Delete this README
```bash
rm TEST_OVERVIEW_README.md
```

That's it! The test page will be completely removed without affecting any core functionality.

## Troubleshooting

**No data showing?**
- Make sure you've imported an Excel file via the "Import Data" page first
- Check that the Excel file is in the `uploads/` folder

**Reload button not working?**
- Verify that an Excel file exists in the `uploads/` folder
- Check browser console for any JavaScript errors

**Calculations seem wrong?**
- Remember: Ireland (IE) is excluded from 90/180-day calculations
- The "days used" is calculated over a rolling 180-day window ending today
- Status colors: 🟢 Safe (<85 days), 🟠 Warning (85-89 days), 🔴 Exceeded (90+ days)

## Files Created
- `test_overview.py` - Flask route and logic
- `templates/test_overview.html` - HTML template with styling
- `TEST_OVERVIEW_README.md` - This file

## Files Modified
- `app.py` - Added blueprint registration (lines 33-40)
- `templates/base.html` - Added sidebar link (lines 84-92)


