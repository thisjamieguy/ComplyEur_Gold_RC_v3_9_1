import os
import json
import secrets
from datetime import timedelta
from flask import Flask
from config import load_config, get_session_lifetime

# Application Version
APP_VERSION = "1.3.0 - Production Ready"

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    
    # Load EU Entry Requirements data at startup
    EU_ENTRY_DATA = []
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_entry_requirements.json')
        with open(data_file_path, 'r', encoding='utf-8') as f:
            EU_ENTRY_DATA = json.load(f)
        print(f"✓ Loaded {len(EU_ENTRY_DATA)} EU entry requirements")
    except Exception as e:
        print(f"Warning: Could not load EU entry requirements data: {e}")

    # Secure secret key from environment variable
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here-change-this-to-a-random-64-character-hex-string':
        # Generate a secure random key if not set
        SECRET_KEY = secrets.token_hex(32)
        print("\n" + "="*70)
        print("WARNING: No SECRET_KEY found in .env file!")
        print("Using a temporary key. Add this to your .env file:")
        print(f"SECRET_KEY={SECRET_KEY}")
        print("="*70 + "\n")

    app.secret_key = SECRET_KEY
    CONFIG = load_config()

    # Configure database
    DATABASE = os.path.join(os.path.dirname(__file__), '..', os.getenv('DATABASE_PATH', 'data/eu_tracker.db'))

    # Make version available to all templates
    @app.context_processor
    def inject_version():
        return dict(app_version=APP_VERSION)

    # Session cookie hardening (essential-only cookie)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    )
    app.permanent_session_lifetime = get_session_lifetime(CONFIG)

    # Additional security headers
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Only add HSTS if using HTTPS
        if hasattr(response, 'request') and response.request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Upload configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # Schengen country code mapping
    COUNTRY_CODE_MAPPING = {
        'AT': 'Austria',
        'BE': 'Belgium',
        'BG': 'Bulgaria',
        'HR': 'Croatia',
        'CY': 'Cyprus',
        'CZ': 'Czech Republic',
        'DK': 'Denmark',
        'EE': 'Estonia',
        'FI': 'Finland',
        'FR': 'France',
        'DE': 'Germany',
        'GR': 'Greece',
        'HU': 'Hungary',
        'IS': 'Iceland',
        'IE': 'Ireland',
        'IT': 'Italy',
        'LV': 'Latvia',
        'LI': 'Liechtenstein',
        'LT': 'Lithuania',
        'LU': 'Luxembourg',
        'MT': 'Malta',
        'NL': 'Netherlands',
        'NO': 'Norway',
        'PL': 'Poland',
        'PT': 'Portugal',
        'RO': 'Romania',
        'SK': 'Slovakia',
        'SI': 'Slovenia',
        'ES': 'Spain',
        'SE': 'Sweden',
        'CH': 'Switzerland'
    }

    # Make variables available to routes
    app.config['EU_ENTRY_DATA'] = EU_ENTRY_DATA
    app.config['DATABASE'] = DATABASE
    app.config['CONFIG'] = CONFIG
    app.config['COUNTRY_CODE_MAPPING'] = COUNTRY_CODE_MAPPING
    app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
