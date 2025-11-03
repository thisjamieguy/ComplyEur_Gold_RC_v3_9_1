#!/usr/bin/env python3
"""
Initialize the SQLite database using Flask-SQLAlchemy.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__init__auth__ import create_app, db
from app import models_auth

def main():
    app = create_app()
    
    # create_app() already initialized the database and created tables
    # Just verify it worked
    with app.app_context():
        from app import models_auth
        if hasattr(models_auth, 'User'):
            user_count = models_auth.User.query.count()
            print(f"✅ Database initialized. User table exists ({user_count} users).")
        else:
            print("✅ Database initialized.")

if __name__ == '__main__':
    main()

