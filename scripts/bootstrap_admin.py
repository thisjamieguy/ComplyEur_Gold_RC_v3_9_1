#!/usr/bin/env python3
"""
Bootstrap admin user with strong random password.
If admin already exists, preserves existing password.
"""

import os
import sys
import secrets
import stat

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.__init__auth__ import create_app, db
from app import models_auth
from app.security import hash_password

def main():
    # Ensure secrets directory exists
    secrets_dir = os.path.join(os.path.dirname(__file__), '..', 'secrets')
    os.makedirs(secrets_dir, exist_ok=True)
    os.chmod(secrets_dir, stat.S_IRWXU)  # 700

    app = create_app()
    
    # Ensure database directory exists
    db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', db_path))
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    with app.app_context():
        # Models are already initialized by create_app()
        User = models_auth.User
        
        # Check if admin exists
        u = User.query.filter_by(username='admin').first()
        
        if u:
            print("ADMIN_USERNAME=admin")
            print("ADMIN_PASSWORD=EXISTS (unchanged)")
        else:
            # Generate a strong password that will pass zxcvbn (score >= 3)
            # Use a mix of words and random chars to ensure high zxcvbn score
            # Format: word-word-word-randomchars to pass both length and complexity
            words = ['secure', 'admin', 'access', 'system', 'protect']
            selected = [secrets.choice(words) for _ in range(3)]
            random_part = secrets.token_urlsafe(16)  # Additional randomness
            temp_pw = '-'.join(selected) + random_part
            
            # Verify it meets requirements before hashing
            from zxcvbn import zxcvbn
            score_check = zxcvbn(temp_pw)
            if score_check['score'] < 3 or len(temp_pw) < 12:
                # Fallback: very long random string (length alone can boost score)
                temp_pw = secrets.token_urlsafe(32) + secrets.token_urlsafe(16)
            
            try:
                # Hash the password
                hashed = hash_password(temp_pw)
                
                # Create user
                u = User(username='admin', password_hash=hashed)
                db.session.add(u)
                db.session.commit()
                
                # Save password to file
                password_file = os.path.join(secrets_dir, 'admin_temp_password.txt')
                with open(password_file, 'w') as f:
                    f.write(temp_pw + '\n')
                os.chmod(password_file, stat.S_IRUSR | stat.S_IWUSR)  # 600
                
                print("ADMIN_USERNAME=admin")
                print(f"ADMIN_PASSWORD={temp_pw}")
                print(f"✅ Saved to {password_file} (chmod 600).")
            except Exception as e:
                print(f"❌ Error creating admin user: {e}")
                import traceback
                traceback.print_exc()
                sys.exit(1)

if __name__ == '__main__':
    main()

