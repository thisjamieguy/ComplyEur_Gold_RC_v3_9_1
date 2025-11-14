"""Authentication application factory and security initialisation for ComplyEur.

Provides CSRF, rate limiting (when available), secure session configuration,
security headers via Talisman, and SQLAlchemy initialisation for auth models.
"""

import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from .config_auth import Config

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:
    Limiter = None


class _NoopLimiter:
    """Fallback limiter when Flask-Limiter is unavailable."""

    def __bool__(self):
        return False

    def init_app(self, app):
        logger = getattr(app, "logger", logging.getLogger(__name__))
        logger.warning("Flask-Limiter not installed; rate limiting disabled")

    def hit(self, *args, **kwargs):
        return True


db = SQLAlchemy()
csrf = CSRFProtect()
if Limiter:
    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
else:
    limiter = _NoopLimiter()


def create_app():
    """Create and configure the authentication Flask application instance."""
    import json
    import logging
    
    # Configure logging early
    log_handlers = [logging.StreamHandler()]
    try:
        logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_handlers.append(logging.FileHandler(os.path.join(logs_dir, 'app.log')))
    except Exception:
        pass
    
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    logger = logging.getLogger(__name__)
    
    # Use absolute paths for template and static folders (matching __init__.py)
    app_dir = os.path.dirname(__file__)
    template_folder = os.path.join(app_dir, 'templates')
    static_folder = os.path.join(app_dir, 'static')
    
    app = Flask(__name__, instance_relative_config=True, 
                static_folder=static_folder, template_folder=template_folder)
    app.config.from_object(Config)
    logger.info(f"Flask app created (template_folder: {template_folder})")
    
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
        logger.exception("EU entry data load failed")
    
    # Schengen country code mapping
    COUNTRY_CODE_MAPPING = {
        'AT': 'Austria', 'BE': 'Belgium', 'BG': 'Bulgaria', 'HR': 'Croatia',
        'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark', 'EE': 'Estonia',
        'FI': 'Finland', 'FR': 'France', 'DE': 'Germany', 'GR': 'Greece',
        'HU': 'Hungary', 'IS': 'Iceland', 'IE': 'Ireland', 'IT': 'Italy',
        'LV': 'Latvia', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg',
        'MT': 'Malta', 'NL': 'Netherlands', 'NO': 'Norway', 'PL': 'Poland',
        'PT': 'Portugal', 'RO': 'Romania', 'SK': 'Slovakia', 'SI': 'Slovenia',
        'ES': 'Spain', 'SE': 'Sweden', 'CH': 'Switzerland'
    }
    
    # Make variables available to routes
    app.config['EU_ENTRY_DATA'] = EU_ENTRY_DATA
    app.config['COUNTRY_CODE_MAPPING'] = COUNTRY_CODE_MAPPING
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
    
    # Upload configuration
    UPLOAD_FOLDER = 'uploads'
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Ensure session is enabled and configured properly for CSRF
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'  # Enterprise security: Strict CSRF protection
    # SESSION_COOKIE_SECURE is set from Config/ENV (False for local HTTP)
    # Explicitly override to ensure it's False for local development
    app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', False)
    # Force Flask to use sessions (needed for CSRF tokens)
    from datetime import timedelta
    app.permanent_session_lifetime = timedelta(hours=8)

    # Fix database path and ensure directory exists BEFORE db.init_app
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        # SQLite URIs: sqlite:///path (absolute) or sqlite:////path (also absolute)
        # sqlite:///./path should be relative but let's handle it explicitly
        db_path = db_uri.replace('sqlite:///', '').replace('sqlite:////', '')
        # Handle ./ prefix for relative paths
        if db_path.startswith('./'):
            db_path = db_path[2:]
        if not os.path.isabs(db_path):
            # Relative to project root
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            db_path = os.path.join(project_root, db_path)
        # Normalize path
        db_path = os.path.normpath(os.path.abspath(db_path))
        # Update config to use absolute path
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        # Ensure parent directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                app.logger.info("Created database directory: %s", db_dir)
            except Exception as e:
                app.logger.error(f"Failed to create database directory {db_dir}: {e}")
                raise

    # DB
    db.init_app(app)


    # CSRF - Enable based on environment (production has HTTPS, local does not)
    # On Render/production, HTTPS is available so CSRF works properly
    is_production = (
        os.getenv('FLASK_ENV') == 'production' or 
        os.getenv('RENDER') == 'true' or
        os.getenv('RENDER_EXTERNAL_HOSTNAME')  # Render sets this automatically
    )
    app.config['WTF_CSRF_ENABLED'] = is_production
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for CSRF tokens
    csrf.init_app(app)
    
    if not is_production:
        # Log CSRF status for local development
        app.logger.warning("CSRF protection %s (local HTTP development)",
                           'ENABLED' if is_production else 'DISABLED')


    # Limiter
    limiter.init_app(app)


    # Security headers via Talisman
    # Detect production environment (HTTPS available)
    # Note: request may not be available at app creation, so check env vars
    is_production = (
        os.getenv('FLASK_ENV') == 'production' or 
        os.getenv('RENDER') == 'true' or
        os.getenv('RENDER_EXTERNAL_HOSTNAME')
    )
    
    # CSP with nonce support (set dynamically per request)
    # Base CSP for Talisman (nonce will be added via after_request hook)
    csp = {
        'default-src': ["'self'"],
        'img-src': ["'self'", "data:"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],  # Allow Bootstrap CSS from CDN
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],  # Allow Bootstrap JS and inline scripts
        'base-uri': ["'none'"],
        'object-src': ["'none'"],
        'frame-ancestors': ["'none'"],
        'form-action': ["'self'"],
    }
    
    # HSTS: 1 year (31536000 seconds) in production only
    hsts_max_age = 31536000 if is_production else 0
    
    Talisman(app,
             content_security_policy=csp,
             force_https=is_production,  # Force HTTPS in production
             force_https_permanent=is_production,
             frame_options='DENY',
             referrer_policy='strict-origin-when-cross-origin',
             strict_transport_security=is_production,  # Enable HSTS in production
             strict_transport_security_max_age=hsts_max_age,
             strict_transport_security_include_subdomains=True)
    
    # CSP nonce support removed - using Talisman's built-in CSP with unsafe-inline for scripts
    # This avoids importing app.core.csp which has heavy cryptography dependencies

    # Initialize Flask-Caching for performance optimization
    try:
        from flask_caching import Cache
        cache_config = {
            'CACHE_TYPE': 'SimpleCache',  # In-memory cache
            'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes default timeout
        }
        cache = Cache(app, config=cache_config)
        app.config['CACHE'] = cache
        logger.info("Flask-Caching initialized successfully")
    except ImportError:
        logger.warning("Flask-Caching not available, caching disabled")
        app.config['CACHE'] = None
    except Exception as e:
        logger.warning(f"Failed to initialize Flask-Caching: {e}")
        app.config['CACHE'] = None

    # Initialize Flask-Compress for gzip compression
    try:
        from flask_compress import Compress
        Compress(app)
        logger.info("Flask-Compress initialized successfully")
    except ImportError:
        logger.warning("Flask-Compress not available, compression disabled")
    except Exception as e:
        logger.warning(f"Failed to initialize Flask-Compress: {e}")

    # Load CONFIG from config module (matching __init__.py behavior)
    try:
        from config import load_config, get_session_lifetime
        CONFIG = load_config()
        app.config['CONFIG'] = CONFIG
        app.permanent_session_lifetime = get_session_lifetime(CONFIG)
        logger.info("Configuration loaded from config module")
    except Exception as e:
        logger.warning(f"Failed to load config from config module: {e}")
        # Fallback to settings.json approach (already in app context block below)
        app.config['CONFIG'] = {
            'RETENTION_MONTHS': 36,
            'SESSION_IDLE_TIMEOUT_MINUTES': 30,
        }
        from datetime import timedelta
        app.permanent_session_lifetime = timedelta(minutes=30)

    # Make version and year available to all templates
    import time
    APP_VERSION = os.getenv('APP_VERSION', '1.7.7')
    _app_start_ts = time.time()
    
    @app.context_processor
    def inject_version():
        from datetime import datetime
        return dict(app_version=APP_VERSION, current_year=datetime.now().year)
    
    # Add custom template filters (matching __init__.py)
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
    
    # Expose country_image_path helper to Jinja
    try:
        from utils.images import country_image_path
        app.jinja_env.globals["country_image_path"] = country_image_path
    except Exception:
        logger.debug("country_image_path helper not available")

    # Initialize models in app context
    with app.app_context():
        from . import models_auth
        models_auth.init_db(db)
        # Create User model after db is initialized
        User = models_auth.get_user_model()
        # Make User available as module attribute
        models_auth.User = User
        db.create_all()
        
        # Create default admin user if no users exist (for fresh deployments)
        try:
            user_count = User.query.count()
            app.logger.info(f"Checking auth database - found {user_count} user(s)")
            
            if user_count == 0:
                from .security import hash_password
                app.logger.info("Creating default admin user...")
                
                # Hash the password
                password_hash = hash_password('admin123')
                app.logger.info(f"Password hashed successfully (length: {len(password_hash)})")
                
                # Create user
                default_admin = User(
                    username='admin',
                    password_hash=password_hash,
                    role='admin'
                )
                db.session.add(default_admin)
                db.session.commit()
                
                # Verify it was created
                verify_count = User.query.count()
                app.logger.info(f"✅ Default admin user created! Database now has {verify_count} user(s)")
                app.logger.info("✅ Login credentials: username=admin, password=admin123")
                app.logger.warning("⚠️  SECURITY: Change the default password immediately after first login!")
            else:
                app.logger.info(f"Auth database already has {user_count} user(s) - skipping default user creation")
                # List usernames for debugging
                try:
                    users = User.query.all()
                    usernames = [u.username for u in users]
                    app.logger.info(f"Existing users: {', '.join(usernames)}")
                except Exception as e:
                    app.logger.warning(f"Could not list users: {e}")
        except Exception as e:
            app.logger.error(f"ERROR creating default admin user: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
            # Don't fail startup if this fails
        
        # Add DATABASE and CONFIG for main routes compatibility
        db_path = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
        if not os.path.isabs(db_path):
            # On Render, use PERSISTENT_DIR if set, otherwise use project root
            persistent_dir = os.getenv('PERSISTENT_DIR')
            if persistent_dir:
                # If PERSISTENT_DIR is set (e.g., /var/data), use it directly
                # Extract just the filename from the path (e.g., 'eu_tracker.db' from 'data/eu_tracker.db')
                db_filename = os.path.basename(db_path)
                db_path = os.path.join(persistent_dir, db_filename)
            else:
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                db_path = os.path.join(project_root, db_path)
        
        # Ensure database directory exists
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
                app.logger.info(f"Created database directory: {db_dir}")
            except Exception as e:
                app.logger.warning(f"Could not create database directory {db_dir}: {e}")
        
        app.config['DATABASE'] = db_path
        app.logger.info(f"Database path configured: {db_path}")
        
        # Initialize main database tables (including legacy admin table)
        try:
            from . import models
            app.logger.info("Initializing main database tables...")
            models.init_db()
            app.logger.info("✅ Main database tables initialized")
        except Exception as e:
            app.logger.error(f"Failed to initialize main database: {e}")
            import traceback
            app.logger.error(traceback.format_exc())
        
        # Load CONFIG from settings.json if available
        try:
            import json
            settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r') as f:
                    app.config['CONFIG'] = json.load(f)
            else:
                # Default config
                app.config['CONFIG'] = {
                    'RETENTION_MONTHS': 36,
                    'SESSION_IDLE_TIMEOUT_MINUTES': 30,
                }
        except Exception:
            app.config['CONFIG'] = {
                'RETENTION_MONTHS': 36,
                'SESSION_IDLE_TIMEOUT_MINUTES': 30,
            }

    # Blueprints - must be after models are initialized
    try:
        from .routes_auth import auth_bp, init_routes
        init_routes(db, csrf, limiter)
        app.register_blueprint(auth_bp)
        app.logger.info("Auth blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register auth blueprint: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        # Don't fail startup - app can work without auth in some cases
    
    # Register main blueprint for dashboard and other routes
    try:
        from .routes import main_bp
        app.register_blueprint(main_bp)
        app.logger.info("Main blueprint registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register main blueprint: {e}")
        import traceback
        app.logger.error(traceback.format_exc())
        # This is critical - re-raise if main routes fail
        raise
    
    # Health check endpoint (no auth required for monitoring)
    try:
        from .routes_health import health_bp
        app.register_blueprint(health_bp)
        app.logger.info("Health blueprint registered successfully")
    except Exception as e:
        app.logger.warning(f"Failed to register health blueprint: {e}")
        # Health check is nice to have but not critical
    
    # Set APP_START_TS and APP_VERSION for health endpoints
    app.config['APP_START_TS'] = _app_start_ts
    app.config['APP_VERSION'] = APP_VERSION
    
    # Register minimal API blueprints for testing (under /api prefix)
    try:
        from .routes_employees import employees_bp
        app.register_blueprint(employees_bp, url_prefix="/api")
        logger.info("Employees API blueprint registered")
    except Exception as e:
        logger.warning(f"Failed to register employees blueprint: {e}")
    
    try:
        from .routes_trips import trips_bp
        app.register_blueprint(trips_bp, url_prefix="/api")
        logger.info("Trips API blueprint registered")
    except Exception as e:
        logger.warning(f"Failed to register trips blueprint: {e}")
    
    # Audit trail dashboard
    try:
        from .routes_audit import audit_bp
        app.register_blueprint(audit_bp)
        logger.info("Audit blueprint registered")
    except Exception as e:
        logger.warning(f"Failed to register audit blueprint: {e}")


    # Jinja filters (match main app filters for consistency)
    @app.template_filter('format_date')
    def format_date_filter(date_str):
        """Convert date strings to DD-MM-YYYY for display.
        Accepts common input formats and returns the original on failure.
        """
        if not date_str:
            return ''
        try:
            from datetime import datetime
            if isinstance(date_str, str):
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y'):
                    try:
                        return datetime.strptime(date_str, fmt).strftime('%d-%m-%Y')
                    except ValueError:
                        continue
            return str(date_str)
        except Exception:
            return str(date_str)

    # Make CSRF token available to all templates
    @app.context_processor
    def inject_csrf_token():
        """Inject CSRF token into template context for forms."""
        try:
            from flask import has_request_context, current_app
            from flask_wtf.csrf import generate_csrf
            
            # Only generate CSRF token if:
            # 1. We're in a request context
            # 2. CSRF is enabled
            # 3. Flask-WTF is initialized
            if (has_request_context() and 
                current_app.config.get('WTF_CSRF_ENABLED', False) and
                hasattr(current_app, 'extensions') and 
                'csrf' in current_app.extensions):
                return {'csrf_token': generate_csrf()}
            else:
                # Return empty string if CSRF not available/needed
                return {'csrf_token': ''}
        except Exception as e:
            # If CSRF is not available, return empty string
            # Log error in debug mode but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"CSRF token generation skipped: {e}")
            return {'csrf_token': ''}

    # CLI - User model is now available
    from . import cli as cli_mod
    cli_mod.init_cli(app, db, models_auth.User)

    # Error handlers (matching __init__.py)
    @app.errorhandler(403)
    def app_forbidden_error(error):
        from flask import render_template
        logger.warning(f"403 error: {error}")
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def app_not_found_error(error):
        from flask import render_template
        logger.warning(f"404 error: {error}")
        return render_template('404.html'), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.error(f"=== 405 METHOD NOT ALLOWED ===")
        from flask import request
        logger.error(f"URL: {request.url}")
        logger.error(f"Method: {request.method}")
        logger.error(f"Endpoint: {request.endpoint}")
        logger.error(f"Available methods for this route: {error.description}")
        logger.error(f"=== END 405 ERROR ===")
        return f"Method {request.method} not allowed for {request.url}", 405

    @app.errorhandler(500)
    def app_internal_error(error):
        """Handle 500 errors gracefully, even if context processors fail."""
        from flask import render_template
        from datetime import datetime
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"500 Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            # Try to render template with error_time
            return render_template('500.html', error_time=error_time), 500
        except Exception as template_error:
            # If template rendering fails, return simple HTML
            logger.error(f"Template rendering failed: {template_error}")
            return f'''
            <!DOCTYPE html>
            <html><head><title>500 - Internal Server Error</title></head>
            <body style="font-family: sans-serif; padding: 40px; text-align: center;">
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong. Please try again later.</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
                <p style="color: #666; font-size: 12px;">Error time: {error_time}</p>
            </body></html>
            ''', 500

    return app
