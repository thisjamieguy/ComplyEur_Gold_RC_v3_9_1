#!/usr/bin/env python3
"""
Local development server for ComplyEur.
Uses the same app factory as Render for consistency.
"""

import os

# Use the same factory as Render (wsgi.py) to ensure identical behavior
from app import create_app

if __name__ == '__main__':
    # Create app using the same factory as production
    app = create_app()
    
    # Local development settings
    port = int(os.getenv('PORT', '5001'))
    host = os.getenv('HOST', '0.0.0.0')
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Run Flask development server (local only - Render uses Gunicorn)
    app.run(debug=debug_mode, host=host, port=port, use_reloader=False)
