"""Utility functions for authentication checks."""

import os
from functools import wraps
from flask import session, jsonify
from datetime import datetime


def login_required(fn):
    """Decorator to require authentication for API endpoints.
    
    Checks session for 'user' or 'user_id' key. Returns 401 JSON if not authenticated.
    Supports EUTRACKER_BYPASS_LOGIN=1 for testing.
    """
    @wraps(fn)
    def _wrap(*args, **kwargs):
        # Temporary developer bypass to speed up manual QA when needed
        try:
            if os.getenv('EUTRACKER_BYPASS_LOGIN') == '1':
                # Set both legacy and new auth system flags
                session['logged_in'] = True
                session['user_id'] = 1  # Set user_id for new auth system
                session['username'] = 'admin'
                session['last_activity'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                # Force session to be permanent so it persists
                session.permanent = True
                return fn(*args, **kwargs)
        except Exception:
            pass
        
        if not session.get("user") and not session.get("user_id"):
            return jsonify({"error": "unauthorized"}), 401
        return fn(*args, **kwargs)
    return _wrap
