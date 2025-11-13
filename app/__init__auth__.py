"""Authentication application factory and security initialisation for ComplyEur.

Provides CSRF, rate limiting (when available), secure session configuration,
security headers via Talisman, and SQLAlchemy initialisation for auth models.
"""

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
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    
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
        import os
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
            os.makedirs(db_dir, exist_ok=True)
            app.logger.info("Created database directory: %s", db_dir)

    # DB
    db.init_app(app)


    # CSRF - Enable based on environment (production has HTTPS, local does not)
    # On Render/production, HTTPS is available so CSRF works properly
    import os  # Ensure os is imported
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
        'style-src': ["'self'", "'unsafe-inline'"],  # Keep unsafe-inline for CSS
        'script-src': ["'self'"],  # Allow scripts from same origin (static files)
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


    # Initialize models in app context
    with app.app_context():
        from . import models_auth
        models_auth.init_db(db)
        # Create User model after db is initialized
        User = models_auth.get_user_model()
        # Make User available as module attribute
        models_auth.User = User
        db.create_all()
        
        # Add DATABASE and CONFIG for main routes compatibility
        import os
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
    import time
    app.config['APP_START_TS'] = time.time()
    # Use version from environment or default
    app.config['APP_VERSION'] = os.getenv('APP_VERSION', '1.7.7')


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


    # CLI - User model is now available
    from . import cli as cli_mod
    cli_mod.init_cli(app, db, models_auth.User)

    # Error handlers
    @app.errorhandler(500)
    def app_internal_error(error):
        from flask import render_template
        from datetime import datetime
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"500 Internal Server Error: {error}")
        logger.error(traceback.format_exc())
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return render_template('500.html', error_time=error_time), 500

    return app
