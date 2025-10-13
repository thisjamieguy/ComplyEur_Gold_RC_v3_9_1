# EU Trip Tracker

A Flask-based web application for managing EU travel compliance under the Schengen Area's 90/180-day rule.

## Overview

The EU Trip Tracker helps organizations monitor employee travel to ensure compliance with the Schengen Area visa-free travel limits. The system tracks trips, calculates rolling 90-day periods within 180-day windows, and provides risk alerts for employees approaching or exceeding limits.

## Features

- 📊 **Trip Management**: Add, edit, and track employee trips across EU countries
- 📈 **Risk Dashboard**: Real-time compliance status with color-coded risk levels
- 📅 **Rolling 90-Day Calculation**: Automatic calculation of days used within sliding 180-day windows
- 🔒 **Security & Privacy**: GDPR-compliant with data retention policies and audit logging
- 📥 **Excel Import/Export**: Bulk upload travel schedules via Excel files
- 📄 **PDF Reports**: Generate compliance reports for individual employees or entire teams
- 🌍 **EU Entry Requirements**: Built-in reference for visa and passport requirements
- ✅ **Trip Validator**: Prevents overlapping trips and validates date ranges

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd eu-trip-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp env_template.txt .env
   # Edit .env and set your SECRET_KEY and ADMIN_PASSWORD
   ```

4. Initialize the database:
   ```bash
   python app.py
   # Database will be created automatically on first run
   ```

## How to Run

### Development Mode

```bash
python app.py
```

The application will start at `http://127.0.0.1:5003` (default port)

### Production Deployment

1. Set `FLASK_ENV=production` in your `.env` file
2. Configure a production WSGI server (gunicorn, uWSGI, etc.)
3. Enable HTTPS and set `SESSION_COOKIE_SECURE=True`

See `/docs/DEPLOYMENT_CHECKLIST.md` for detailed production setup instructions.

## Documentation

Comprehensive documentation is available in the `/docs` folder:

- **SETUP_GUIDE.md** - Detailed setup and configuration
- **DEPLOYMENT_CHECKLIST.md** - Production deployment guide
- **COMPLIANCE.md** - GDPR compliance features
- **IMPORT_SYSTEM_README.md** - Excel import instructions
- **SECURITY_REVIEW_SUMMARY.md** - Security features overview

## Project Structure

```
eu-trip-tracker/
├── app.py                 # Main Flask application
├── config.py              # Configuration loader
├── requirements.txt       # Python dependencies
├── modules/               # Service modules
│   └── app/services/      # Business logic (rolling90, exports, etc.)
├── templates/             # Jinja2 HTML templates
├── static/                # CSS, JavaScript, images
├── data/                  # JSON data files
├── docs/                  # Project documentation
└── tests/                 # Unit tests
```

## License

This project is for internal use. All rights reserved.

## Author

Developed for EU travel compliance management.

## Support

For questions or issues, please refer to the documentation in `/docs` or contact the system administrator.

