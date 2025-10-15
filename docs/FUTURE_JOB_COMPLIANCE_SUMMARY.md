# Future Job Compliance Forecast Feature - Implementation Summary

## Overview
This feature provides forward-looking compliance checking for future scheduled jobs based on the 90/180 day EU rolling window rule. It helps identify potential compliance issues before they happen, considering both past trips and other scheduled future trips.

## Features Implemented

### 1. Core Compliance Forecast Service
**File:** `modules/app/services/compliance_forecast.py`

A comprehensive calculation engine that:
- Calculates days used in 180-day window before a future job starts
- Includes all past trips + future trips scheduled before the job
- Determines risk levels: GREEN (<80 days), YELLOW (80-89 days), RED (≥90 days)
- Calculates "compliant from" date when a non-compliant job would become compliant
- Uses configurable warning threshold from settings
- Respects Schengen vs non-Schengen countries (Ireland excluded)

**Key Functions:**
- `calculate_future_job_compliance()` - Main forecast calculator
- `get_all_future_jobs_for_employee()` - Get forecasts for all future trips
- `calculate_what_if_scenario()` - Test hypothetical trips
- `calculate_compliant_from_date()` - Find when employee becomes compliant

### 2. Future Job Alerts Page
**Route:** `/future-job-alerts`
**Template:** `templates/future_job_alerts.html`

A dedicated page showing all at-risk future jobs with:
- **Summary Cards:** Count of red/yellow/green jobs
- **Sortable Table:** 
  - Sort by: Risk Level (default), Date, Employee Name, Days Used
  - Filter by: All Levels, Critical Only, Warning Only, Safe Only
- **Color-Coded Rows:** Red, yellow, green backgrounds based on risk
- **Detailed Information:**
  - Employee name (links to detail page)
  - Job dates and country
  - Days used at job start
  - Days after job completes
  - Days remaining
  - Compliant from date (if non-compliant)
- **Hover Tooltips:** Show detailed breakdown with contributing trips
- **Export Button:** Export to Excel with color coding

### 3. What-If Scenario Tool
**Routes:** 
- `/what-if-scenario` - Main page
- `/api/calculate-scenario` - API endpoint

**Locations:**
- Standalone page (`templates/what_if_scenario.html`)
- Employee detail page (existing planning tool leverages same API)

**Features:**
- Select employee from dropdown
- Input hypothetical trip dates and country
- Calculate compliance status in real-time
- Shows:
  - Risk badge (GREEN/YELLOW/RED)
  - Job duration
  - Days used before/after
  - Days remaining
  - Compliant from date (if applicable)
  - Recommendation advice
- Schengen country detection (Ireland handled correctly)
- Form validation (end date must be after start date)

### 4. Admin Settings - Warning Threshold
**Template:** `templates/admin_settings.html`
**Config Key:** `FUTURE_JOB_WARNING_THRESHOLD`

New admin setting:
- **Field:** Warning Threshold (days)
- **Default:** 80 days
- **Validation:** Must be between 1-90
- **Description:** Show yellow warning when future trips would use this many days or more
- **Behavior:** Red warnings always show for trips exceeding 90 days

### 5. Export Functionality
**Route:** `/export-future-alerts`

Exports future job alerts to Excel with:
- All forecast data (employee, dates, country, duration, days used/remaining, risk level)
- Color-coded rows (red/yellow/green backgrounds)
- Auto-adjusted column widths
- Sorted by risk level (critical first)
- Filename includes timestamp
- Audit log entry created

### 6. Visual Indicators Across Existing Views

#### A. Employee Detail Page
**Enhanced:** `templates/employee_detail.html`

For each future trip:
- **Risk Badge:** Shows in Status column with emoji (🔴/🟡/🟢) and days used
- **Compliance Warning Row:** Appears below non-compliant trips showing:
  - Warning message with days used
  - "Employee will be compliant again from: [DATE]"
  - Color-coded background (red/yellow/green)

#### B. Dashboard
**Enhanced:** `templates/dashboard.html` and `app.py` (dashboard route)

New widget:
- **Future Compliance Alerts Summary Card**
- Shows counts: Red (critical), Yellow (warning), Green (safe)
- Buttons: "View All Future Alerts" and "Test What-If Scenario"
- Warning banner if any red alerts exist
- Positioned after "At Risk Alert Section"

#### C. Navigation
**Enhanced:** `templates/base.html`

Added sidebar links:
- **Future Job Alerts** (with warning triangle icon)
- **What-If Scenario** (with question mark icon)
- Positioned after Calendar link

### 7. Styling & UI Components

All styling implemented using inline styles and existing CSS classes:
- **Risk Badges:** Color-coded pills with emoji indicators
- **Summary Cards:** Gradient backgrounds with border accents
- **Tooltips:** Dark background with white text (hover on table cells)
- **Buttons:** Primary (blue), outline, and danger styles
- **Tables:** Responsive with hover effects
- **Forms:** Clean inputs with focus states
- **Responsive:** Mobile-friendly grid layouts

## Configuration

### Default Settings (`config.py`)
```python
DEFAULTS = {
    # ... existing settings ...
    'FUTURE_JOB_WARNING_THRESHOLD': 80  # Warn when future trips would use 80+ days
}
```

### Admin can customize:
- Go to **Settings** page
- Find **Future Job Compliance Forecast** section
- Adjust warning threshold (1-90 days)
- Save settings

## Risk Level Logic

### Green (Safe)
- Days used < 80 (default threshold)
- Employee can safely complete the trip
- No action required

### Yellow (Warning)
- Days used ≥ 80 but < 90
- Approaching the limit
- Exercise caution, consider shorter duration

### Red (Critical)
- Days used ≥ 90
- Would exceed EU limit
- **Do NOT schedule** - reschedule to compliant date

## Usage Workflow

### For Planning Future Work:
1. **Dashboard** → See summary of future alerts
2. **Future Job Alerts** → View detailed list of all future jobs
3. **Filter & Sort** → Focus on critical issues
4. **Export** → Share with stakeholders
5. **What-If Tool** → Test alternative dates

### For Testing Scenarios:
1. **What-If Scenario** page
2. Select employee
3. Enter hypothetical trip details
4. Calculate compliance
5. Review recommendation
6. Adjust dates as needed

### For Individual Employees:
1. **Employee Detail** page
2. View future trips with risk badges
3. See compliance warnings inline
4. Use built-in planning tool
5. Adjust trips as needed

## Technical Notes

### Database Queries
- No new tables required (uses existing trips table)
- Calculations done in Python using existing `rolling90` module
- Efficient: Only calculates for employees with future trips

### Performance
- Dashboard loads future forecasts for all employees (may be slower with many employees)
- Individual employee pages only calculate for that employee
- Caching could be added in future if needed

### Audit Logging
- Future alerts export action logged
- Settings changes logged (threshold updates)

## Files Created
1. `modules/app/services/compliance_forecast.py` - Core service
2. `templates/future_job_alerts.html` - Alerts page
3. `templates/what_if_scenario.html` - What-if tool

## Files Modified
1. `app.py` - Added routes and updated employee_detail/dashboard
2. `config.py` - Added warning threshold default
3. `templates/admin_settings.html` - Added threshold setting
4. `templates/employee_detail.html` - Added forecast indicators
5. `templates/dashboard.html` - Added summary widget
6. `templates/base.html` - Added navigation links

## Testing Recommendations

1. **Add future trips** for an employee
2. **Check dashboard** - should see summary widget
3. **Visit Future Job Alerts** - should see trips listed
4. **Test filtering and sorting**
5. **Export to Excel** - verify color coding
6. **Use What-If tool** - test various scenarios
7. **Adjust warning threshold** in settings - verify yellow warnings update
8. **Visit employee detail** - see inline risk badges
9. **Test Ireland trips** - should not count toward limit

## Future Enhancements (Optional)

1. Email alerts for critical future jobs
2. Calendar view integration (visual indicators on calendar events)
3. Bulk rescheduling tool
4. Historical forecast accuracy tracking
5. Team-level forecasts (multiple employees)
6. Mobile app integration

## Support

For questions or issues:
- Check `docs/HELP_SYSTEM_COMPLETE.md` for general help
- Review `modules/app/services/compliance_forecast.py` for calculation logic
- Check `logs/audit.log` for export and settings change history


