# EU 90/180 Employee Travel Tracker

A comprehensive web application for tracking employee travel within the EU/Schengen area to ensure compliance with the 90-day rule within any 180-day period.

## 🚀 New Features Added

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

## 🛠️ Installation & Setup

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

## 📖 How to Use

### 1. Excel Import Process
1. Navigate to Dashboard
2. Click "📊 Import Excel" button
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

## 🔍 Import Error Handling

The system will flag these issues:
- **Employee not found**: Name doesn't match existing employees
- **Invalid country code**: Unrecognized 2-letter code
- **Invalid date format**: Not YYYY-MM-DD or DD/MM/YYYY
- **Date logic errors**: Entry date after exit date
- **Duplicate trips**: Same employee, dates, and country
- **Missing data**: Empty required fields

## 🏗️ File Structure

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

## 🔧 Technical Details

### Database Schema
- **employees**: id, name
- **trips**: id, employee_id, country, entry_date, exit_date
- **admin**: id, password_hash

### Key Functions
- `parse_excel_file()`: Excel parsing and validation
- `find_employee_by_name()`: Case-insensitive employee matching
- `trip_exists()`: Duplicate detection
- `calculate_eu_days()`: 90/180 rule calculation

### Security Features
- **File validation**: Only Excel files allowed
- **SQL injection protection**: Parameterized queries
- **Session-based authentication**: Admin login required
- **Input sanitization**: Secure filename handling

## 🔐 GDPR Enhancements

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

## 🐛 Troubleshooting

### Common Issues
1. **Excel file not uploading**: Check file format (.xlsx/.xls only)
2. **Employee not found**: Ensure employee names match exactly (case-insensitive)
3. **Country code errors**: Use 2-letter ISO codes only
4. **Date format issues**: Use YYYY-MM-DD or DD/MM/YYYY formats

### Debug Mode
The app runs in debug mode by default. Check the console for detailed error messages.

## 📞 Support

For issues or questions:
1. Check the console output for error messages
2. Verify Excel file format matches requirements
3. Ensure all dependencies are installed correctly

---

**Version**: 2.0 with Excel Import & Dashboard Sorting
**Author**: Claude Code Assistant
**License**: MIT