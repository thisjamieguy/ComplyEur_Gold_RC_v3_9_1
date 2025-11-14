import os
import json
from datetime import timedelta, date


DEFAULTS = {
    'RETENTION_MONTHS': 36,
    'SESSION_IDLE_TIMEOUT_MINUTES': 30,
    'PASSWORD_HASH_SCHEME': 'argon2',
    'DSAR_EXPORT_DIR': './exports',
    'AUDIT_LOG_PATH': './logs/audit.log',
    'SESSION_COOKIE_SECURE': False,
    'TEST_MODE': False,  # Toggle to enable/disable test pages
    'CALENDAR_DEV_MODE': False,  # Enable calendar in development (hidden from production)
    'RISK_THRESHOLDS': {
        'green': 30,  # >= 30 days remaining = green
        'amber': 10   # 10-29 days remaining = amber, < 10 = red
    },
    'FUTURE_JOB_WARNING_THRESHOLD': 80,  # Warn when future trips would use 80+ days
    'NEWS_FILTER_REGION': 'EU_ONLY',  # News filtering: EU_ONLY or ALL
    'ADMIN_EMAIL': None
}


SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')


def ensure_directories(config: dict) -> None:
    # Determine persistent base directory (prefer PERSISTENT_DIR, else next to DB)
    db_path_env = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
    persistent_base = os.path.abspath(
        os.getenv('PERSISTENT_DIR', os.path.dirname(os.path.abspath(db_path_env)))
    )

    # Resolve exports directory: ENV > config > default; make absolute under persistent_base if relative
    exports_env = os.getenv('EXPORT_DIR')
    exports_dir = exports_env or config.get('DSAR_EXPORT_DIR', DEFAULTS['DSAR_EXPORT_DIR'])
    if not os.path.isabs(exports_dir):
        exports_dir = os.path.join(persistent_base, exports_dir)
    exports_dir = os.path.abspath(exports_dir)
    config['DSAR_EXPORT_DIR'] = exports_dir

    # Resolve audit log path: ENV > config > default; make absolute under persistent_base if relative
    audit_env = os.getenv('AUDIT_LOG_PATH')
    logs_path = audit_env or config.get('AUDIT_LOG_PATH', DEFAULTS['AUDIT_LOG_PATH'])
    if not os.path.isabs(logs_path):
        logs_path = os.path.join(persistent_base, logs_path)
    logs_path = os.path.abspath(logs_path)
    config['AUDIT_LOG_PATH'] = logs_path

    logs_dir = os.path.dirname(logs_path)
    compliance_dir = os.path.join(os.path.dirname(__file__), 'compliance')

    os.makedirs(exports_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(compliance_dir, exist_ok=True)


def load_config() -> dict:
    config = DEFAULTS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    config.update(data)
        except Exception:
            pass
    ensure_directories(config)
    return config


def save_config(updated: dict) -> dict:
    config = load_config()
    config.update(updated)
    # normalize types
    try:
        config['RETENTION_MONTHS'] = int(config.get('RETENTION_MONTHS', DEFAULTS['RETENTION_MONTHS']))
        config['SESSION_IDLE_TIMEOUT_MINUTES'] = int(config.get('SESSION_IDLE_TIMEOUT_MINUTES', DEFAULTS['SESSION_IDLE_TIMEOUT_MINUTES']))
        config['SESSION_COOKIE_SECURE'] = bool(config.get('SESSION_COOKIE_SECURE', DEFAULTS['SESSION_COOKIE_SECURE']))
    except Exception:
        pass
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    ensure_directories(config)
    return config


def get_session_lifetime(config: dict) -> timedelta:
    minutes = int(config.get('SESSION_IDLE_TIMEOUT_MINUTES', DEFAULTS['SESSION_IDLE_TIMEOUT_MINUTES']))
    return timedelta(minutes=minutes)



