"""Shared blueprint, services, and helpers for ComplyEur web routes."""

from __future__ import annotations

import atexit
import csv
import hashlib
import io
import json
import logging
import os
import re
import secrets
import signal
import sqlite3
import time
import traceback
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Blueprint, current_app
from werkzeug.utils import secure_filename

from app.middleware.auth import current_user
from config import get_session_lifetime, load_config, save_config
from app.runtime_env import build_runtime_state

logger = logging.getLogger(__name__)

try:
    from app.services.hashing import Hasher
    logger.info("Successfully imported hashing service")
except Exception as exc:  # pragma: no cover
    logger.error(f"Failed to import hashing service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.audit import write_audit
    logger.info("Successfully imported audit service")
except Exception as exc:
    logger.error(f"Failed to import audit service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.retention import purge_expired_trips, get_expired_trips, anonymize_employee
    logger.info("Successfully imported retention service")
except Exception as exc:
    logger.error(f"Failed to import retention service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.dsar import create_dsar_export, delete_employee_data, rectify_employee_name, get_employee_data
    logger.info("Successfully imported dsar service")
except Exception as exc:
    logger.error(f"Failed to import dsar service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.exports import export_trips_csv, export_employee_report_pdf, export_all_employees_report_pdf
    logger.info("Successfully imported exports service")
except Exception as exc:
    logger.error(f"Failed to import exports service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.rolling90 import (
        presence_days,
        days_used_in_window,
        earliest_safe_entry,
        calculate_days_remaining,
        get_risk_level,
        days_until_compliant,
    )
    logger.info("Successfully imported rolling90 service")
except Exception as exc:
    logger.error(f"Failed to import rolling90 service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.trip_validator import validate_trip, validate_date_range
    logger.info("Successfully imported trip_validator service")
except Exception as exc:
    logger.error(f"Failed to import trip_validator service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.compliance_forecast import (
        calculate_future_job_compliance,
        get_all_future_jobs_for_employee,
        calculate_what_if_scenario,
        get_risk_level_for_forecast,
    )
    logger.info("Successfully imported compliance_forecast service")
except Exception as exc:
    logger.error(f"Failed to import compliance_forecast service: {exc}")
    logger.error(traceback.format_exc())
    raise

try:
    from app.services.backup import create_backup, auto_backup_if_needed, list_backups
    logger.info("Successfully imported backup service")
except Exception as exc:
    logger.error(f"Failed to import backup service: {exc}")
    logger.error(traceback.format_exc())
    raise

load_dotenv()
main_bp = Blueprint('main', __name__)


def redact_private_trip_data(trip):
    """Redact private trip data for admin display."""
    if trip.get('is_private', False):
        return {
            'entry_date': trip['entry_date'],
            'exit_date': trip['exit_date'],
            'country': 'Personal Trip',
            'is_private': True,
        }
    return trip


LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 300  # 5 minutes


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(current_app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def current_actor(default: str = 'admin') -> str:
    """Return username for audit logging."""
    user = current_user()
    if user and getattr(user, 'username', None):
        return user.username  # type: ignore[attr-defined]
    return default


def verify_and_upgrade_password(stored_hash, password):
    """Verify password and upgrade hash if needed."""
    try:
        hasher = Hasher()
        if hasher.verify(stored_hash, password):
            if not stored_hash.startswith('$argon2'):
                new_hash = hasher.hash(password)
                return True, new_hash
            return True, None
    except Exception:
        pass
    return False, None


def allowed_file(filename):
    """Check if file extension is allowed."""
    try:
        allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'xlsx', 'xls'})
    except (RuntimeError, KeyError):
        allowed_extensions = {'xlsx', 'xls'}

    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions


__all__ = [
    'main_bp',
    'logger',
    'Hasher',
    'write_audit',
    'purge_expired_trips',
    'get_expired_trips',
    'anonymize_employee',
    'create_dsar_export',
    'delete_employee_data',
    'rectify_employee_name',
    'get_employee_data',
    'export_trips_csv',
    'export_employee_report_pdf',
    'export_all_employees_report_pdf',
    'presence_days',
    'days_used_in_window',
    'earliest_safe_entry',
    'calculate_days_remaining',
    'get_risk_level',
    'days_until_compliant',
    'validate_trip',
    'validate_date_range',
    'calculate_future_job_compliance',
    'get_all_future_jobs_for_employee',
    'calculate_what_if_scenario',
    'get_risk_level_for_forecast',
    'create_backup',
    'auto_backup_if_needed',
    'list_backups',
    'load_config',
    'get_session_lifetime',
    'save_config',
    'build_runtime_state',
    'LOGIN_ATTEMPTS',
    'MAX_ATTEMPTS',
    'ATTEMPT_WINDOW_SECONDS',
    'redact_private_trip_data',
    'get_db',
    'current_actor',
    'verify_and_upgrade_password',
    'allowed_file',
    'atexit',
    'csv',
    'hashlib',
    'io',
    'json',
    'os',
    're',
    'secrets',
    'signal',
    'time',
    'zipfile',
    'datetime',
    'timedelta',
    'date',
    'Path',
    'Optional',
    'secure_filename',
]
