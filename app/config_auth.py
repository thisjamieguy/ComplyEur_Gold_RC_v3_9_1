import os
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()


class Config:
    _secret_key = os.getenv("SECRET_KEY")
    if not _secret_key:
        import secrets
        _secret_key = secrets.token_hex(32)
    SECRET_KEY = _secret_key
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    SESSION_COOKIE_HTTPONLY = True
    # For local development, SESSION_COOKIE_SECURE should be False (HTTP not HTTPS)
    # In production, set SESSION_COOKIE_SECURE=true in .env
    SESSION_COOKIE_SECURE = str(os.getenv("SESSION_COOKIE_SECURE","false")).lower() == "true"
    SESSION_COOKIE_SAMESITE = "Strict"  # Enterprise security: Strict CSRF protection
    
    # Password policy
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", "12"))
    PASSWORD_MIN_ENTROPY = int(os.getenv("PASSWORD_MIN_ENTROPY", "3"))  # zxcvbn score 0-4
    
    # WTF-CSRF configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    WTF_CSRF_CHECK_DEFAULT = True


    AUTH_TOTP_ENABLED = str(os.getenv("AUTH_TOTP_ENABLED","true")).lower() == "true"


    ARGON2_MEMORY = int(os.getenv("ARGON2_MEMORY", 65536))
    ARGON2_TIME = int(os.getenv("ARGON2_TIME", 3))
    ARGON2_PARALLELISM = int(os.getenv("ARGON2_PARALLELISM", 2))


    RATE_PER_IP = os.getenv("RATE_PER_IP", "5 per minute")
    RATE_PER_USERNAME = os.getenv("RATE_PER_USERNAME", "10 per 15 minutes")


    IDLE_TIMEOUT = timedelta(minutes=int(os.getenv("IDLE_TIMEOUT_MINUTES", 15)))
    ABSOLUTE_TIMEOUT = timedelta(hours=int(os.getenv("ABSOLUTE_TIMEOUT_HOURS", 8)))

