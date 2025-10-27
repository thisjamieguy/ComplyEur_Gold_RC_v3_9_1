# EU 90/180 Employee Travel Tracker v1.5.1

A Flask web application for tracking employee travel to EU/Schengen countries and ensuring compliance with the 90/180-day rule.

## Features

- **Employee Management**: Add and manage employee records
- **Trip Tracking**: Record and track EU/Schengen trips with entry/exit dates
- **Compliance Monitoring**: Real-time calculation of days used and remaining in the 90/180-day rolling window
- **Risk Assessment**: Color-coded risk levels (green/amber/red) based on remaining days
- **Calendar View**: Visual calendar showing trip history and future compliance dates
- **Data Export**: Export trip data to CSV and generate PDF reports
- **GDPR Compliance**: Built-in data retention and DSAR (Data Subject Access Request) tools
- **Security**: Secure authentication, audit logging, and session management

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please refer to the help section within the application or contact the development team.