import os
import json
import secrets
import logging
import traceback
from datetime import timedelta
from flask import Flask, request, render_template
from config import load_config, get_session_lifetime

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Application Version
APP_VERSION = "1.6.1"

def create_app():
    """Application factory pattern"""
    # Configure logging
    # Ensure logs directory exists
    logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    log_handlers = [logging.StreamHandler()]
    try:
        log_handlers.append(logging.FileHandler(os.path.join(logs_dir, 'app.log')))
    except Exception:
        # If file logging fails, continue with console logging only
        pass

    # Respect LOG_LEVEL from environment (default INFO)
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting application initialization...")
        app = Flask(__name__, static_folder='static', template_folder='templates')
        logger.info("Flask app created successfully")
    except Exception as e:
        logger.error(f"Failed to create Flask app: {e}")
        logger.error(traceback.format_exc())
        raise
    
    # Load EU Entry Requirements data at startup
    EU_ENTRY_DATA = []
    try:
        logger.info("Loading EU entry requirements data...")
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_entry_requirements.json')
        logger.info(f"Looking for data file at: {data_file_path}")
        with open(data_file_path, 'r', encoding='utf-8') as f:
            EU_ENTRY_DATA = json.load(f)
        logger.info(f"Loaded {len(EU_ENTRY_DATA)} EU entry requirements")
    except Exception as e:
        logger.error(f"Failed to load EU entry requirements data: {e}")
        logger.error(traceback.format_exc())

    # Secure secret key from environment variable
    try:
        logger.info("Setting up secret key...")
        SECRET_KEY = os.getenv('SECRET_KEY')
        if not SECRET_KEY or SECRET_KEY == 'your-secret-key-here-change-this-to-a-random-64-character-hex-string':
            # Generate a secure random key if not set
            SECRET_KEY = secrets.token_hex(32)
            logger.warning("No SECRET_KEY found in environment, generating temporary key")

        app.secret_key = SECRET_KEY
        logger.info("Secret key configured successfully")
        
        logger.info("Loading configuration...")
        CONFIG = load_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to setup secret key or load config: {e}")
        logger.error(traceback.format_exc())
        raise

    # Configure database
    try:
        logger.info("Configuring database...")
        db_path = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
        if not os.path.isabs(db_path):
            # Make relative paths absolute from project root
            DATABASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))
        else:
            DATABASE = db_path
        logger.info(f"Database path: {DATABASE}")
        
        # Check if database directory exists
        db_dir = os.path.dirname(DATABASE)
        if not os.path.exists(db_dir):
            logger.info(f"Creating database directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)

        # Initialize database tables
        logger.info("Importing models module...")
        from .models import init_db
        logger.info("Models module imported successfully")
        
        # Set the database path in app config before calling init_db
        app.config['DATABASE'] = DATABASE
        logger.info("Database path set in app config")
        
        # Initialize database within app context
        logger.info("Initializing database tables...")
        with app.app_context():
            init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error(traceback.format_exc())
        logger.warning(f"Continuing without DB initialization: {e}")
        # Don't raise here, let the app continue with limited functionality

    # Make version and CSRF token available to all templates
    @app.context_processor
    def inject_version():
        return dict(app_version=APP_VERSION)
    
    @app.context_processor
    def inject_csrf_token():
        """Generate CSRF token for forms"""
        import secrets
        return {'csrf_token': secrets.token_hex(32)}

    # Session cookie hardening (essential-only cookie)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    )
    # Explicitly control DEBUG via env (default False)
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.permanent_session_lifetime = get_session_lifetime(CONFIG)

    # Additional security headers
    @app.after_request
    def set_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Only add HSTS if using HTTPS
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Global error handler for 405 Method Not Allowed
    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.error(f"=== 405 METHOD NOT ALLOWED ===")
        logger.error(f"URL: {request.url}")
        logger.error(f"Method: {request.method}")
        logger.error(f"Endpoint: {request.endpoint}")
        logger.error(f"Available methods for this route: {error.description}")
        logger.error(f"=== END 405 ERROR ===")
        return f"Method {request.method} not allowed for {request.url}", 405

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

    # Add custom template filters
    @app.template_filter('country_name')
    def country_name_filter(country_code):
        """Convert country code to full country name"""
        return COUNTRY_CODE_MAPPING.get(country_code, country_code)
    
    @app.template_filter('is_ireland')
    def is_ireland_filter(country_code):
        """Return True if the country code represents Ireland (IE)."""
        if not country_code:
            return False
        try:
            return str(country_code).strip().upper() in ['IE', 'IRELAND']
        except Exception:
            return False

    @app.template_filter('format_date')
    def format_date_filter(date_str):
        """Convert date string to DD-MM-YYYY format for user display (UK regional standard)"""
        if not date_str:
            return ''
        try:
            from datetime import datetime
            if isinstance(date_str, str):
                # Try different date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        date_obj = datetime.strptime(date_str, fmt)
                        return date_obj.strftime('%d-%m-%Y')
                    except ValueError:
                        continue
            return str(date_str)
        except Exception:
            return str(date_str)

    @app.template_filter('format_ddmmyyyy')
    def format_ddmmyyyy_filter(dt):
        """Format datetime object to DD-MM-YYYY string"""
        if not dt:
            return ''
        try:
            from .services.date_utils import format_ddmmyyyy
            return format_ddmmyyyy(dt)
        except Exception:
            return str(dt)

    # Close DB connection at app context teardown
    @app.teardown_appcontext
    def close_db(exception):
        try:
            from flask import g
            conn = getattr(g, '_db_conn', None)
            if conn is not None:
                conn.close()
        except Exception:
            pass

    # Expose helpers to Jinja
    try:
        from utils.images import country_image_path
        app.jinja_env.globals["country_image_path"] = country_image_path
    except Exception:
        # If helper import fails, continue without it
        pass

    # Register blueprints
    try:
        logger.info("Importing routes module...")
        from .routes import main_bp
        logger.info("Routes module imported successfully")

        logger.info("Registering blueprint...")
        app.register_blueprint(main_bp)
        logger.info("Blueprint registered successfully")

        logger.info(f"Registered {len(list(app.url_map.iter_rules()))} routes successfully")
    except Exception as e:
        logger.error(f"Failed to register routes: {e}")
        logger.error(traceback.format_exc())
        raise

    logger.info("Application initialization completed successfully")

    # Register CLI commands
    @app.cli.command('news-fetch')
    def news_fetch_command():
        """Fetch fresh news from RSS feeds"""
        try:
            from .services.news_fetcher import fetch_news_from_sources, clear_old_news
            with app.app_context():
                db_path = app.config['DATABASE']
                items = fetch_news_from_sources(db_path)
                print(f"✓ Fetched {len(items)} news items")
                
                # Clean up old news (older than 7 days)
                clear_old_news(db_path, days_to_keep=7)
                print("✓ Cleaned up old news items")
        except Exception as e:
            logger.error(f"Error fetching news: {e}")
            print(f"✗ Error: {e}")

    # Global error handlers (ensure friendly pages for non-blueprint routes)
    @app.errorhandler(404)
    def app_not_found_error(error):
        logger.warning(f"404 error: {error}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def app_internal_error(error):
        logger.error(f"500 Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        return render_template('500.html'), 500

    return app
