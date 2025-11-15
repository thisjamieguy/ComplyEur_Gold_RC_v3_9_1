"""Unified ComplyEur application factory."""

from __future__ import annotations

import copy
import json
import logging
import os
import time
import traceback
from datetime import timedelta

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv():
        return False
from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf import CSRFProtect

from config import DEFAULTS as CONFIG_DEFAULTS
from config import get_session_lifetime, load_config
from .config_auth import Config as AuthConfig
from .runtime_env import build_runtime_state, require_env_vars

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:  # pragma: no cover - optional dependency
    Limiter = None

load_dotenv()

APP_VERSION = os.getenv('APP_VERSION', '1.7.7')
_app_start_ts = time.time()

db = SQLAlchemy()
csrf = CSRFProtect()
if Limiter:
    limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
else:  # pragma: no cover - fallback
    class _NoopLimiter:
        def __bool__(self):
            return False

        def init_app(self, app):
            app.logger.warning("Flask-Limiter not installed; rate limiting disabled")

        def hit(self, *args, **kwargs):
            return True

    limiter = _NoopLimiter()


def _load_country_codes():
    return {
        'AT': 'Austria', 'BE': 'Belgium', 'BG': 'Bulgaria', 'HR': 'Croatia',
        'CY': 'Cyprus', 'CZ': 'Czech Republic', 'DK': 'Denmark', 'EE': 'Estonia',
        'FI': 'Finland', 'FR': 'France', 'DE': 'Germany', 'GR': 'Greece',
        'HU': 'Hungary', 'IS': 'Iceland', 'IE': 'Ireland', 'IT': 'Italy',
        'LV': 'Latvia', 'LI': 'Liechtenstein', 'LT': 'Lithuania', 'LU': 'Luxembourg',
        'MT': 'Malta', 'NL': 'Netherlands', 'NO': 'Norway', 'PL': 'Poland',
        'PT': 'Portugal', 'RO': 'Romania', 'SK': 'Slovakia', 'SI': 'Slovenia',
        'ES': 'Spain', 'SE': 'Sweden', 'CH': 'Switzerland'
    }


def _setup_logging(runtime_state):
    log_handlers = [logging.StreamHandler()]
    try:
        log_handlers.append(logging.FileHandler(runtime_state.log_file))
    except Exception:
        pass

    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers,
    )
    return logging.getLogger(__name__)


def _init_cache(app):
    try:
        from flask_caching import Cache
        cache_config = {
            'CACHE_TYPE': 'SimpleCache',
            'CACHE_DEFAULT_TIMEOUT': 300,
        }
        cache = Cache(app, config=cache_config)
        app.config['CACHE'] = cache
        app.logger.info("Flask-Caching initialized successfully")
    except ImportError:
        app.logger.warning("Flask-Caching not available, caching disabled")
        app.config['CACHE'] = None
    except Exception as exc:
        app.logger.warning("Failed to initialize Flask-Caching: %s", exc)
        app.config['CACHE'] = None


def _init_compress(app):
    try:
        from flask_compress import Compress
        Compress(app)
        app.logger.info("Flask-Compress initialized successfully")
    except ImportError:
        app.logger.warning("Flask-Compress not available, compression disabled")
    except Exception as exc:
        app.logger.warning("Failed to initialize Flask-Compress: %s", exc)


def _register_template_helpers(app, country_codes):
    @app.template_filter('country_name')
    def country_name_filter(code):
        return country_codes.get(code, code)

    @app.template_filter('is_ireland')
    def is_ireland_filter(code):
        if not code:
            return False
        try:
            return str(code).strip().upper() in {'IE', 'IRELAND'}
        except Exception:
            return False

    @app.template_filter('format_date')
    def format_date_filter(date_str):
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

    @app.template_filter('format_ddmmyyyy')
    def format_ddmmyyyy_filter(value):
        if not value:
            return ''
        try:
            from .services.date_utils import format_ddmmyyyy
            return format_ddmmyyyy(value)
        except Exception:
            return str(value)

    try:
        from utils.images import country_image_path
        app.jinja_env.globals['country_image_path'] = country_image_path
    except Exception:
        app.logger.debug("country_image_path helper not available")


def _register_context_processors(app):
    @app.context_processor
    def inject_version():
        from datetime import datetime
        return dict(app_version=APP_VERSION, current_year=datetime.now().year)

    @app.context_processor
    def inject_csrf_token():
        try:
            from flask import has_request_context, current_app
            from flask_wtf.csrf import generate_csrf
            if (has_request_context() and current_app.config.get('WTF_CSRF_ENABLED', False)
                    and 'csrf' in getattr(current_app, 'extensions', {})):
                return {'csrf_token': generate_csrf()}
            return {'csrf_token': ''}
        except Exception as exc:
            app.logger.debug("CSRF token generation skipped: %s", exc)
            return {'csrf_token': ''}


def _register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning("403 error: %s", error)
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        app.logger.warning("404 error: %s", error)
        return render_template('404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        from flask import request
        app.logger.error("405 on %s %s", request.method, request.url)
        return f"Method {request.method} not allowed for {request.url}", 405

    @app.errorhandler(500)
    def internal_error(error):
        from datetime import datetime
        app.logger.error("500 Internal Server Error: %s", error)
        app.logger.error(traceback.format_exc())
        error_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            return render_template('500.html', error_time=error_time), 500
        except Exception as exc:
            app.logger.error("Failed to render 500 template: %s", exc)
            return ("<h1>500 - Internal Server Error</h1>"
                    f"<p>Error time: {error_time}</p>"), 500


def _register_security_headers(app):
    @app.after_request
    def set_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' data: https://cdn.jsdelivr.net; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        response.headers['Content-Security-Policy'] = csp_policy

        if request.endpoint == 'static' or request.path.startswith('/static/'):
            response.cache_control.max_age = 31536000
            response.cache_control.public = True
        elif request.endpoint in {'main.sitemap', 'main.robots'}:
            response.cache_control.max_age = 86400
            response.cache_control.public = True
        else:
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True

        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response


def _register_cli(app):
    @app.cli.command('news-fetch')
    def news_fetch_command():
        from .services.news_fetcher import fetch_news_from_sources, clear_old_news
        try:
            with app.app_context():
                db_path = app.config['DATABASE']
                items = fetch_news_from_sources(db_path)
                app.logger.info("Fetched %d news items", len(items))
                clear_old_news(db_path, days_to_keep=7)
        except Exception as exc:
            app.logger.error("News fetch command failed: %s", exc)


def _init_models(app):
    from . import models_auth, models
    models_auth.init_db(db)
    with app.app_context():
        user_model = models_auth.get_user_model()
        models_auth.User = user_model
        db.create_all()
        models.init_db()
        try:
            models.sync_admin_password_from_env()
        except Exception as exc:
            app.logger.error("Admin credential bootstrap failed: %s", exc)
            raise


def _register_blueprints(app):
    from .routes import main_bp
    from .routes_audit import audit_bp
    from .routes_auth import auth_bp, init_routes
    from .routes_employees import employees_bp
    from .routes_trips import trips_bp
    from .routes_health import health_bp

    init_routes(db, csrf, limiter)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(employees_bp, url_prefix='/api')
    app.register_blueprint(trips_bp, url_prefix='/api')


def _start_background_services(app):
    try:
        from .services.alerts import start_alert_scheduler
        start_alert_scheduler(app)
    except Exception as exc:
        app.logger.warning("Alert scheduler unavailable: %s", exc)

    try:
        if os.getenv('REQUEST_TIMING', 'false').lower() == 'true':
            from .utils.timing import init_request_timing
            init_request_timing(app)
            app.logger.info("Request timing middleware enabled")
    except Exception as exc:
        app.logger.warning("Failed to enable request timing: %s", exc)


def create_app():
    """Create and configure the ComplyEur Flask application."""
    require_env_vars()
    runtime_state = build_runtime_state(force_refresh=True)
    logger = _setup_logging(runtime_state)

    app_dir = os.path.dirname(__file__)
    template_folder = os.path.join(app_dir, 'templates')
    static_folder = os.path.join(app_dir, 'static')

    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=static_folder,
        template_folder=template_folder,
    )
    app.config.from_object(AuthConfig)
    app.logger = logger

    app.config['DATABASE'] = str(runtime_state.database_path)
    app.config['SQLALCHEMY_DATABASE_URI'] = runtime_state.sqlalchemy_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    try:
        config_data = load_config()
    except Exception as exc:
        logger.warning("Failed to load settings.json; using defaults: %s", exc)
        config_data = copy.deepcopy(CONFIG_DEFAULTS)

    app.config['CONFIG'] = config_data
    try:
        app.permanent_session_lifetime = get_session_lifetime(config_data)
    except Exception as exc:
        logger.warning("Failed to apply session lifetime: %s", exc)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    is_production = bool(
        os.getenv('FLASK_ENV') == 'production'
        or os.getenv('RENDER') == 'true'
        or os.getenv('RENDER_EXTERNAL_HOSTNAME')
    )
    app.config['WTF_CSRF_ENABLED'] = is_production
    app.config['WTF_CSRF_TIME_LIMIT'] = None

    Talisman(
        app,
        content_security_policy={
            'default-src': ["'self'"],
            'img-src': ["'self'", "data:"],
            'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            'script-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
            'base-uri': ["'none'"],
            'object-src': ["'none'"],
            'frame-ancestors': ["'none'"],
            'form-action': ["'self'"],
        },
        force_https=is_production,
        force_https_permanent=is_production,
        frame_options='DENY',
        referrer_policy='strict-origin-when-cross-origin',
        strict_transport_security=is_production,
        strict_transport_security_max_age=31536000 if is_production else 0,
        strict_transport_security_include_subdomains=True,
    )

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict',
        SESSION_COOKIE_SECURE=app.config.get('SESSION_COOKIE_SECURE', False),
    )

    eu_entry_data = []
    try:
        data_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'eu_entry_requirements.json')
        with open(data_file_path, 'r', encoding='utf-8') as data_file:
            eu_entry_data = json.load(data_file)
        app.logger.info("Loaded %d EU entry requirements", len(eu_entry_data))
    except Exception as exc:
        app.logger.error("Failed to load EU entry requirements data: %s", exc)

    country_codes = _load_country_codes()
    upload_dir = config_data.get('UPLOAD_DIR') or str(runtime_state.directories['uploads'])
    app.config['UPLOAD_FOLDER'] = upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    app.config['EU_ENTRY_DATA'] = eu_entry_data
    app.config['COUNTRY_CODE_MAPPING'] = country_codes
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}
    app.config['APP_START_TS'] = _app_start_ts
    app.config['APP_VERSION'] = APP_VERSION

    _init_cache(app)
    _init_compress(app)
    _register_template_helpers(app, country_codes)
    _register_context_processors(app)
    _register_error_handlers(app)
    _register_security_headers(app)
    _register_cli(app)
    _init_models(app)
    _register_blueprints(app)
    _start_background_services(app)

    return app


__all__ = ['create_app', 'db', 'csrf', 'limiter']
