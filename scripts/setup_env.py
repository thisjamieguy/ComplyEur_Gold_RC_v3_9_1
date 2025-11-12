#!/usr/bin/env python3
"""
Setup .env file with secure defaults.
If .env exists, ensures required keys are present.
If .env.example exists, copies from it first.
"""

import os
import shutil
import secrets

def ensure_key_value(lines, key, value):
    """Append key=value if key not present, or update if present."""
    found = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f'{key}='):
            lines[i] = f'{key}={value}'
            found = True
            break
    if not found:
        lines.append(f'{key}={value}')
    return lines

def main():
    # Create .env from .env.example if needed
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copyfile('.env.example', '.env')
            print("✅ Copied .env.example to .env")
        else:
            # Create empty .env
            with open('.env', 'w') as f:
                f.write('')
            print("✅ Created empty .env file")

    # Read existing .env
    lines = []
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            lines = f.read().splitlines()

    # Generate SECRET_KEY if missing or placeholder
    key = secrets.token_urlsafe(48)  # ~64 chars url-safe
    
    # Replace existing SECRET_KEY or add one
    found_secret = False
    for i, line in enumerate(lines):
        if line.strip().startswith('SECRET_KEY='):
            existing_val = line.split('=', 1)[1].strip()
            # Replace if placeholder or empty
            if not existing_val or 'change-this' in existing_val.lower() or 'your-secret-key' in existing_val.lower():
                lines[i] = f'SECRET_KEY={key}'
                found_secret = True
                print("✅ Generated new SECRET_KEY")
            else:
                print("✅ SECRET_KEY already set (preserved)")
                found_secret = True
            break
    
    if not found_secret:
        lines.append(f'SECRET_KEY={key}')
        print("✅ Added SECRET_KEY")

    # Ensure secure defaults
    ensure_key_value(lines, 'AUTH_TOTP_ENABLED', 'true')
    # SESSION_COOKIE_SECURE=false for local development (HTTP)
    # Set to 'true' in production when using HTTPS
    ensure_key_value(lines, 'SESSION_COOKIE_SECURE', 'false')
    ensure_key_value(lines, 'IDLE_TIMEOUT_MINUTES', '15')
    ensure_key_value(lines, 'ABSOLUTE_TIMEOUT_HOURS', '8')
    
    # Ensure SQLALCHEMY_DATABASE_URI is set (use relative path format)
    # sqlite:///./ means relative to current working directory
    db_path = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///./data/auth.db')
    ensure_key_value(lines, 'SQLALCHEMY_DATABASE_URI', db_path)

    # Write back
    with open('.env', 'w') as f:
        f.write('\n'.join(lines) + '\n')

    print('✅ .env is ready with secure defaults.')

if __name__ == '__main__':
    main()

