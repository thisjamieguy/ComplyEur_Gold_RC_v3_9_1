# EU 90/180 Employee Travel Tracker v1.6.4

A Flask web application for tracking employee travel to EU/Schengen countries and ensuring compliance with the 90/180-day rule.

## Features

- **Employee Management**: Add and manage employee records
- **Trip Tracking**: Record and track EU/Schengen trips with entry/exit dates
- **Compliance Monitoring**: Real-time calculation of days used and remaining in the 90/180-day rolling window
- **Risk Assessment**: Color-coded risk levels (green/amber/red) based on remaining days
- **Calendar View**: Visual calendar showing trip history and future compliance dates
- **Interactive Calendar**: Drag-and-drop trip management with mobile touch support
- **Trip Reassignment**: Move trips between employees with conflict validation
- **Data Export**: Export trip data to CSV and generate PDF reports
- **GDPR Compliance**: Built-in data retention and DSAR (Data Subject Access Request) tools
- **Security**: Secure authentication, audit logging, and session management
- **EU Travel News**: Real-time news feed filtered for EU/Schengen travel advisories and policy updates
- **Comprehensive Testing**: Automated test suite for calendar functionality

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd eu-trip-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python run_local.py
   ```

5. **Access the application**
   Open your browser to `http://localhost:5000`

### Production Deployment on Render

1. **Connect your GitHub repository to Render**
2. **Create a new Web Service**
3. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
4. **Set environment variables:**
   - `SECRET_KEY`: A secure random string
   - `DATABASE_PATH`: `data/eu_tracker.db` (or your preferred path)
   - `SESSION_COOKIE_SECURE`: `true` (for HTTPS)
5. **Deploy**

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key for sessions (required)
- `DATABASE_PATH`: Path to SQLite database file (default: `data/eu_tracker.db`)
- `SESSION_COOKIE_SECURE`: Enable secure cookies for HTTPS (default: `false`)

### Application Settings

The application includes configurable settings accessible through the admin panel:

- **Data Retention**: Configure how long to keep employee data
- **Session Timeout**: Set automatic logout timeout
- **Risk Thresholds**: Customize green/amber/red risk levels
- **Future Job Warnings**: Set threshold for future job compliance alerts

## Database Schema

### Employees Table
- `id`: Primary key
- `name`: Employee full name
- `created_at`: Timestamp

### Trips Table
- `id`: Primary key
- `employee_id`: Foreign key to employees
- `country`: EU/Schengen country code
- `entry_date`: Date of entry
- `exit_date`: Date of exit
- `purpose`: Trip purpose (optional)
- `created_at`: Timestamp

### Admin Table
- `id`: Primary key (always 1)
- `password_hash`: Hashed admin password
- `created_at`: Timestamp

## API Endpoints

### Authentication
- `GET /login` - Login page
- `POST /login` - Authenticate user
- `GET /logout` - Logout user

### Main Application
- `GET /dashboard` - Main dashboard
- `GET /employee/<id>` - Employee detail page
- `POST /add_employee` - Add new employee
- `POST /add_trip` - Add new trip
- `POST /delete_trip/<id>` - Delete trip

### API Endpoints
- `GET /api/entry-requirements` - Get EU entry requirements data
- `POST /api/entry-requirements/reload` - Reload entry requirements

## Security Features

- **Password Hashing**: Uses Argon2 for secure password storage
- **Session Security**: HTTPOnly cookies, secure flags, session timeout
- **Rate Limiting**: Login attempt rate limiting
- **Security Headers**: XSS protection, content type options, frame options
- **Audit Logging**: Comprehensive audit trail for all actions
- **Data Retention**: Automatic purging of expired data
- **GDPR Compliance**: DSAR tools and data anonymization

## Development

### Project Structure

```
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # Route definitions
│   ├── models.py            # Database models
│   ├── services/            # Business logic services
│   ├── templates/           # Jinja2 templates
│   └── static/              # Static assets (CSS, JS, images)
├── data/                    # Data files and database
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── Procfile                 # Render deployment config
├── runtime.txt              # Python version
└── README.md               # This file
```

### Services

- **hashing.py**: Password hashing utilities
- **audit.py**: Audit logging functionality
- **rolling90.py**: 90/180-day rule calculations
- **trip_validator.py**: Trip data validation
- **exports.py**: Data export functionality
- **compliance_forecast.py**: Future compliance forecasting
- **dsar.py**: GDPR data subject access requests
- **retention.py**: Data retention and anonymization
- **backup.py**: Database backup functionality
- **news_fetcher.py**: EU travel news filtering and RSS feed management

## News Filtering System

The application includes an intelligent news filtering system that displays only EU/Schengen-relevant travel news and advisories.

### Features

- **EU Country Filtering**: Automatically filters news for all EU27 countries plus Iceland, Norway, Switzerland, and Liechtenstein
- **EU Policy Keywords**: Detects EU-wide policy updates including ETIAS, EES, Schengen, and European Commission announcements
- **Country Aliases**: Supports country name variations (e.g., "Czechia"/"Czech Republic", "Netherlands"/"Holland")
- **Case-Insensitive**: Works with any text case and unicode characters
- **Admin Controls**: Toggle between EU-only and all-regions news filtering

### Configuration

#### Environment Variables

Set the news filter region in your environment:

```bash
# Filter to EU/Schengen only (default)
NEWS_FILTER_REGION=EU_ONLY

# Show all regions
NEWS_FILTER_REGION=ALL
```

#### Admin Settings

1. **Via Settings Modal**: Click your profile → Settings → General → News Filter
2. **Via Home Page Toggle**: Use the quick toggle buttons on the home page header (admin only)

### News Sources

The system automatically seeds per-country GOV.UK travel advice feeds for all EU/Schengen countries:

- **EU Commission Feeds**: European Commission News, EU Home Affairs
- **Country-Specific Feeds**: Individual GOV.UK travel advice for each EU/Schengen country
- **Global Feeds**: Disabled by default, can be enabled via admin settings

### Adding/Removing Countries

To modify the country allow-list, edit `app/services/news_fetcher.py`:

```python
EU_COUNTRIES = {
    "Country Name": ["Country Name", "Alias 1", "Alias 2"],
    # Add new countries here
}
```

### Adding/Removing Keywords

To modify EU-wide keywords, edit `app/services/news_fetcher.py`:

```python
EU_KEYWORDS = [
    "schengen", "etias", "ees", "european commission", "eu", 
    "home affairs", "border checks", "visa waiver"
    # Add new keywords here
]
```

### Testing

## Calendar Features (v1.6.4)

### Interactive Calendar
The calendar now supports advanced interaction features:

- **Drag-and-Drop**: Move trips between dates and employees
- **Trip Resizing**: Resize trips by dragging the edges
- **Mobile Touch Support**: Full touch support for mobile devices
- **Trip Reassignment**: Move trips between different employees
- **Conflict Validation**: Prevents overlapping trips
- **Visual Feedback**: Real-time visual feedback during interactions

### Testing the Calendar

Access the comprehensive test suite at `/calendar_test`:

1. **Navigate to Test Page**: Go to `http://localhost:5000/calendar_test`
2. **Generate Mock Data**: Click "Generate Mock Data" to create test data
3. **Run Tests**: Click "Run All Tests" to execute the full test suite
4. **Individual Tests**: Run specific tests using individual "Run" buttons

### Test Coverage
The test suite covers:
- ✅ Calendar rendering and display
- ✅ Trip block visibility and positioning
- ✅ Statistics display accuracy
- ✅ Drag-and-drop functionality
- ✅ Trip resizing operations
- ✅ Mobile touch interactions
- ✅ Conflict validation
- ✅ Performance benchmarks

### Known Issues and Fixes

**v1.6.4 Visual QA**: Native calendar timeline validated with accessible color tokens and automated Playwright coverage
- **Issue**: Legacy trip bars failed to render after API migration
- **Fix**: Updated rendering pipeline, ensured DOM containers/styles match native calendar implementation
- **Result**: All trips render with status colors (green/orange/red) and hover tooltips across the six-month view

Run the news filter tests:

```bash
python3 -m pytest tests/test_news_filter.py -v
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please refer to the help section within the application or contact the development team.
