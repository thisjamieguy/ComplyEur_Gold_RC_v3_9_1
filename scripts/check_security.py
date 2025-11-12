#!/usr/bin/env python3
"""
Security Check Script
Verifies authentication, environment variables, and production security settings.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / '.env')

def check_env_secrets():
    """Check that .env contains no plaintext secrets"""
    issues = []
    env_file = PROJECT_ROOT / '.env'
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        return issues
    
    with open(env_file, 'r') as f:
        lines = f.readlines()
    
    # Check for common secret patterns
    secret_patterns = ['password', 'secret', 'key', 'token', 'api_key']
    for i, line in enumerate(lines, 1):
        line_lower = line.lower()
        # Skip comments and empty lines
        if line.strip().startswith('#') or not line.strip():
            continue
        # Check if line contains a secret pattern but is not set to a placeholder
        for pattern in secret_patterns:
            if pattern in line_lower and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                # Check if value is not a placeholder
                if value and value not in ['', 'your-secret-key', 'your-password', 'your-api-key']:
                    # Check if it looks like a real secret (not just a variable reference)
                    if not value.startswith('${') and len(value) > 8:
                        issues.append(f"Line {i}: Potential secret found in {key.strip()}")
    
    return issues

def check_auth_bypass():
    """Check that auth bypass is only enabled in test mode"""
    bypass_enabled = os.getenv('EUTRACKER_BYPASS_LOGIN') == '1'
    is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER') == 'true'
    
    issues = []
    if bypass_enabled and is_production:
        issues.append("⚠️  AUTH BYPASS ENABLED IN PRODUCTION - This is a security risk!")
    elif bypass_enabled:
        print("ℹ️  Auth bypass enabled (acceptable for testing)")
    
    return issues

def check_session_security():
    """Check session security settings"""
    issues = []
    
    # Check session cookie secure flag
    session_secure = os.getenv('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    is_production = os.getenv('FLASK_ENV') == 'production' or os.getenv('RENDER') == 'true'
    
    if is_production and not session_secure:
        issues.append("⚠️  SESSION_COOKIE_SECURE should be 'true' in production")
    elif not is_production and session_secure:
        print("ℹ️  SESSION_COOKIE_SECURE is 'true' (will fail in local HTTP development)")
    
    # Check secret key
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        issues.append("⚠️  SECRET_KEY is not set")
    elif len(secret_key) < 32:
        issues.append("⚠️  SECRET_KEY should be at least 32 characters long")
    
    return issues

def check_database_security():
    """Check database security settings"""
    issues = []
    
    # Check database path
    db_path = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
    if not os.path.isabs(db_path):
        db_path = str(PROJECT_ROOT / db_path)
    
    # Check if database file is readable by others
    if os.path.exists(db_path):
        stat = os.stat(db_path)
        # Check file permissions (should be 600 or 644)
        mode = stat.st_mode & 0o777
        if mode & 0o007:  # World readable/writable
            issues.append(f"⚠️  Database file is world-accessible (mode: {oct(mode)})")
    
    return issues

def check_admin_password():
    """Check that admin password is not default"""
    issues = []
    
    # Check if admin password is set
    admin_password = os.getenv('ADMIN_PASSWORD')
    if admin_password and admin_password in ['admin', 'admin123', 'password', '123456']:
        issues.append("⚠️  Admin password appears to be a default/weak password")
    
    return issues

def main():
    """Main execution"""
    print("=" * 80)
    print("Security Check")
    print("=" * 80)
    print()
    
    all_issues = []
    
    # Check environment secrets
    print("1. Checking environment secrets...")
    env_issues = check_env_secrets()
    if env_issues:
        all_issues.extend(env_issues)
        for issue in env_issues:
            print(f"   {issue}")
    else:
        print("   ✅ No plaintext secrets found in .env")
    print()
    
    # Check auth bypass
    print("2. Checking authentication bypass...")
    bypass_issues = check_auth_bypass()
    if bypass_issues:
        all_issues.extend(bypass_issues)
        for issue in bypass_issues:
            print(f"   {issue}")
    else:
        print("   ✅ Auth bypass check passed")
    print()
    
    # Check session security
    print("3. Checking session security...")
    session_issues = check_session_security()
    if session_issues:
        all_issues.extend(session_issues)
        for issue in session_issues:
            print(f"   {issue}")
    else:
        print("   ✅ Session security check passed")
    print()
    
    # Check database security
    print("4. Checking database security...")
    db_issues = check_database_security()
    if db_issues:
        all_issues.extend(db_issues)
        for issue in db_issues:
            print(f"   {issue}")
    else:
        print("   ✅ Database security check passed")
    print()
    
    # Check admin password
    print("5. Checking admin password...")
    admin_issues = check_admin_password()
    if admin_issues:
        all_issues.extend(admin_issues)
        for issue in admin_issues:
            print(f"   {issue}")
    else:
        print("   ✅ Admin password check passed")
    print()
    
    # Summary
    print("=" * 80)
    print("Security Check Summary")
    print("=" * 80)
    if all_issues:
        print(f"❌ Found {len(all_issues)} security issues")
        return 1
    else:
        print("✅ All security checks passed")
        return 0

if __name__ == '__main__':
    sys.exit(main())

