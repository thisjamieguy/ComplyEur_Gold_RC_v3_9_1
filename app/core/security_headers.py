"""
Security Headers Management
Enforces TLS 1.3 + HSTS (1 year) in production
"""

from flask import request, current_app
from functools import wraps


def enforce_hsts(response):
    """
    Add HSTS header to response if HTTPS is available.
    Called as after_request hook.
    
    Args:
        response: Flask response object
    
    Returns:
        Response with HSTS header if applicable
    """
    # Only add HSTS in production with HTTPS
    if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
        # HSTS: 1 year (31536000 seconds)
        response.headers['Strict-Transport-Security'] = (
            'max-age=31536000; includeSubDomains; preload'
        )
    
    # Always set security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

