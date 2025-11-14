import os
import json
from datetime import timedelta, date

from app.runtime_env import build_runtime_state


DEFAULTS = {
    'RETENTION_MONTHS': 36,
    'SESSION_IDLE_TIMEOUT_MINUTES': 30,
    'PASSWORD_HASH_SCHEME': 'argon2',
    'DSAR_EXPORT_DIR': './exports',
    'AUDIT_LOG_PATH': './logs/audit.log',
    'UPLOAD_DIR': './uploads',
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
    """Populate config paths using the shared runtime state."""
    state = build_runtime_state()
    config['DSAR_EXPORT_DIR'] = str(state.directories['exports'])
    config['UPLOAD_DIR'] = str(state.directories['uploads'])
    config['AUDIT_LOG_PATH'] = str(state.audit_log_file)
    # Ensure compliance dir remains available next to repo (non-persistent content)
    compliance_dir = os.path.join(os.path.dirname(__file__), 'compliance')
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



