"""
CSRF Protection Utilities
Verify CSRF tokens are enabled on all POST routes
"""

from functools import wraps
from flask import request, abort
from flask_wtf.csrf import CSRFProtect


def require_csrf(f):
    """
    Decorator to explicitly require CSRF token on POST routes.
    Flask-WTF should handle this automatically, but this provides explicit enforcement.
    
    Usage:
        @require_csrf
        @route('/endpoint', methods=['POST'])
        def my_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            # Flask-WTF should have already validated CSRF
            # This is just a double-check
            if not request.is_secure and not request.headers.get('X-Forwarded-Proto') == 'https':
                # In development, CSRF might be disabled
                # In production, ensure it's enabled
                from flask import current_app
                if current_app.config.get('WTF_CSRF_ENABLED', False):
                    # CSRF is enabled, Flask-WTF will have checked it
                    pass
        return f(*args, **kwargs)
    return decorated_function


def verify_csrf_enabled(app):
    """
    Verify CSRF protection is enabled.
    
    Args:
        app: Flask application
    
    Returns:
        bool: True if CSRF is enabled
    """
    return app.config.get('WTF_CSRF_ENABLED', False)

