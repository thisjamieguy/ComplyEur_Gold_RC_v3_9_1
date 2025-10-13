# EU 90/180 Employee Travel Tracker

A comprehensive web application for tracking employee travel within the EU/Schengen area to ensure compliance with the 90-day rule within any 180-day period.

## Latest Compliance Features (v1.2)

### 1. Earliest Next Safe Entry Date
- **Automatic calculation** of when an employee can safely re-enter Schengen
- Shows "Eligible Now" if under 90 days or the exact date when safe to re-enter
- Displayed on:
  - Dashboard (below employee name)
  - Employee detail page (prominent card display)
  - Card view (highlighted section)
- **Logic**: Calculates rolling 180-day window to find first date where days used ≤ 89

### 2. Risk Bar + Color Coding
- **Visual risk indicator** showing days remaining with color-coded bar
- **Color thresholds** (configurable in `config.py`):
  - **Green**: ≥ 30 days remaining (Safe)
  - **Amber**: 10-29 days remaining (Caution)
  - **Red**: < 10 days remaining (High Risk)
- Displayed on:
  - Dashboard table (new "Days Remaining" column with progress bar)
  - Card view (color-coded border and bar)
  - Employee detail page (summary stats)
- **Tooltip**: Shows "X of 90 days used" on hover

### 3. Trip Validator (Overlaps & Date Logic)
- **Hard errors** (blocks save):
  - Exit date before entry date
  - Overlapping trips for same employee
- **Soft warnings** (allows override with reason):
  - Missing exit date (ongoing trip)
  - Trip longer than 90 days
- **UI behavior**:
  - Hard errors show red message and block save
  - Soft warnings show amber message with "Override" option
  - Override requires reason stored in `validation_note` field
- **Validation display**:
  - Inline messages in trip form
  - Override notes shown in trip history table
  - Audit trail of all validation overrides

## Previous Features

### 1. Excel Auto-Import
- **Upload Excel files** (.xlsx/.xls) with trip data
- **Auto-detection** of employee names, countries, and dates
- **Country code mapping** (DE → Germany, FR → France, etc.)
- **Duplicate prevention** and error handling
- **Preview before import** with confirmation step

### 2. Dashboard Sorting & Table View
- **Sortable table view** with clickable column headers
- **Sort by**: Employee name, trip count, days used, next trip
- **Toggle between** table and card views
- **Real-time sorting** with visual indicators

## 📋 Excel File Requirements

### File Format
- **Supported formats**: .xlsx or .xls
- **Headers** (optional but recommended): Employee Name, Country, Entry Date, Exit Date
- **Default column order**: Name, Country Code, Entry Date, Exit Date

### Data Requirements
- **Employee names**: Must match existing employees in the system (case-insensitive)
- **Country codes**: Use 2-letter ISO codes (DE, FR, ES, IT, etc.)
- **Date formats**: YYYY-MM-DD or DD/MM/YYYY
- **Date validation**: Entry date must be before exit date

### Example Excel File
```
Employee Name | Country | Entry Date | Exit Date
John Smith    | DE      | 2024-01-15 | 2024-01-22
Jane Doe      | FR      | 15/02/2024 | 25/02/2024
Bob Johnson   | ES      | 2024-03-05 | 2024-03-12
```

## 🌍 Supported Countries (31 Schengen Area)

| Code | Country | Code | Country | Code | Country |
|------|---------|------|---------|------|---------|
| AT | Austria | BE | Belgium | BG | Bulgaria |
| HR | Croatia | CY | Cyprus | CZ | Czech Republic |
| DK | Denmark | EE | Estonia | FI | Finland |
| FR | France | DE | Germany | GR | Greece |
| HU | Hungary | IS | Iceland | IE | Ireland |
| IT | Italy | LV | Latvia | LI | Liechtenstein |
| LT | Lithuania | LU | Luxembourg | MT | Malta |
| NL | Netherlands | NO | Norway | PL | Poland |
| PT | Portugal | RO | Romania | SK | Slovakia |
| SI | Slovenia | ES | Spain | SE | Sweden |
| CH | Switzerland |

## Installation & Setup

### Prerequisites
```bash
Python 3.7+
pip (Python package manager)
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
python3 app.py
```

The application will be available at: http://127.0.0.1:5001

**Default admin password**: `admin123`

## How to Use

### 1. Excel Import Process
1. Navigate to Dashboard
2. Click "Import Excel" button
3. Select your Excel file (.xlsx or .xls)
4. Review the preview screen showing:
   - Valid trips ready for import
   - Any errors or warnings
5. Click "Confirm Import" to save trips

### 2. Dashboard Views
- **Table View** (default): Sortable columns, compact display
- **Card View**: Visual cards with progress bars
- Toggle between views using the buttons

### 3. Sorting Options
Click any column header to sort:
- **Name**: A-Z or Z-A
- **Trips**: Trip count ascending/descending
- **Days Used**: EU days used ascending/descending
- **Next Trip**: Upcoming trips by date

## Import Error Handling

The system will flag these issues:
- **Employee not found**: Name doesn't match existing employees
- **Invalid country code**: Unrecognized 2-letter code
- **Invalid date format**: Not YYYY-MM-DD or DD/MM/YYYY
- **Date logic errors**: Entry date after exit date
- **Duplicate trips**: Same employee, dates, and country
- **Missing data**: Empty required fields

## File Structure

```
eu-trip-tracker/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── README.md                      # This file
├── eu_tracker.db                  # SQLite database (created automatically)
├── uploads/                       # Excel file upload directory
└── templates/
    ├── dashboard.html             # Main dashboard with table/card views
    ├── import_excel.html          # Excel upload page
    ├── import_preview.html        # Import preview and confirmation
    ├── employee_detail.html       # Individual employee details
    ├── bulk_add_trip.html         # Bulk trip adding
    └── calendar.html              # Calendar timeline view
```

## Technical Details

### Database Schema
- **employees**: id, name
- **trips**: id, employee_id, country, entry_date, exit_date, validation_note, created_at
- **admin**: id, password_hash

### New Compliance Modules
- **app/services/rolling90.py**: Rolling 90/180 day calculations
  - `presence_days()`: Extract all Schengen days from trips
  - `days_used_in_window()`: Count days in rolling 180-day window
  - `earliest_safe_entry()`: Calculate earliest safe re-entry date
  - `calculate_days_remaining()`: Days remaining before limit
  - `get_risk_level()`: Determine green/amber/red risk level

- **app/services/trip_validator.py**: Trip validation logic
  - `validate_trip()`: Validate against overlap and date rules
  - `check_trip_overlaps()`: Detect overlapping trips
  - `validate_date_range()`: Validate date logic

### Configuration
- **config.py**: Centralized settings including:
  - `RISK_THRESHOLDS`: Color thresholds (green: 30, amber: 10)
  - Can be customized without code changes
  - Stored in `settings.json` for persistence

### Key Functions
- `parse_excel_file()`: Excel parsing and validation
- `find_employee_by_name()`: Case-insensitive employee matching
- `trip_exists()`: Duplicate detection
- `calculate_eu_days()`: Legacy 90/180 rule calculation (deprecated in favor of rolling90 module)

### Security Features
- **File validation**: Only Excel files allowed
- **SQL injection protection**: Parameterized queries
- **Session-based authentication**: Admin login required
- **Input sanitization**: Secure filename handling
- **Validation audit trail**: All overrides logged with reasons

## GDPR Enhancements

This app includes the following GDPR-focused features:

- Privacy Policy at `/privacy` (footer link in the UI)
- Cookie consent banner for functional storage (sidebar collapse preference)
- DSAR export endpoint (requires login):
  - `GET /api/dsar/export?employee_id=<id>` or `?employee_name=<name>` → downloads JSON
- DSAR delete endpoint (requires login):
  - `POST /api/dsar/delete` with JSON `{ "employee_id": <id> }` or `{ "employee_name": "Name" }`
- Session cookie hardening: HttpOnly + SameSite=Lax (enable `SESSION_COOKIE_SECURE=True` in production)

Data processed:
- Employee name; trip country, entry/exit dates, travel days; admin password hash

Cookies/local storage:
- Essential: Flask session cookie for authentication
- Optional (functional): `localStorage.sidebarCollapsed` (only if consented)

Data subject requests:
- Admins can export and delete per-employee data using the endpoints above.

## Testing

### Run Unit Tests
Test the compliance features with comprehensive unit tests:

```bash
# Test rolling 90/180 day calculations
python -m pytest test_rolling90.py -v

# Test trip validation logic
python -m pytest test_trip_validator.py -v

# Run all tests
python -m pytest test_*.py -v
```

Or use unittest:

```bash
python test_rolling90.py
python test_trip_validator.py
```

### Test Coverage
- **Rolling90 Tests**: 30+ test cases covering:
  - Presence day calculations
  - Rolling window day counts
  - Earliest safe entry date logic
  - Risk level determination
  - Edge cases (gaps, overlaps, continuous presence)

- **Validator Tests**: 25+ test cases covering:
  - Date range validation
  - Overlap detection
  - Trip exclusion (for edits)
  - Soft warnings vs hard errors
  - Edge cases (touching trips, one-day trips)

### Manual Testing Checklist
- [ ] Add employee with 85 days used → verify amber/red bar
- [ ] Add overlapping trip → see blocking error message
- [ ] Add trip > 90 days → see warning with override option
- [ ] Override warning with reason → verify note appears in trip history
- [ ] Check earliest safe entry shows on dashboard
- [ ] Verify risk colors: green (≥30 days), amber (10-29), red (<10)

## Troubleshooting

### Common Issues
1. **Excel file not uploading**: Check file format (.xlsx/.xls only)
2. **Employee not found**: Ensure employee names match exactly (case-insensitive)
3. **Country code errors**: Use 2-letter ISO codes only
4. **Date format issues**: Use YYYY-MM-DD or DD/MM/YYYY formats
5. **Trip overlap errors**: Check existing trips for date conflicts
6. **Risk bar not showing**: Ensure employee has trips in last 180 days

### Debug Mode
The app runs in debug mode by default. Check the console for detailed error messages.

## Support

For issues or questions:
1. Check the console output for error messages
2. Verify Excel file format matches requirements
3. Ensure all dependencies are installed correctly

---

**Version**: 1.2 with Compliance Features (Earliest Safe Entry, Risk Bars, Trip Validator)
**Previous**: 2.0 with Excel Import & Dashboard Sorting
**Author**: Claude Code Assistant
**License**: MIT