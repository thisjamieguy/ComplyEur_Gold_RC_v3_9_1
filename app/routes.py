from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash, make_response, send_file
import hashlib
import sqlite3
import logging
import traceback
from datetime import datetime, timedelta, date
import os
import re
from pathlib import Path
from typing import Optional
from werkzeug.utils import secure_filename
from config import load_config, get_session_lifetime, save_config
import time
import io
import csv
import zipfile
import secrets
import json
import atexit
import signal
from dotenv import load_dotenv
from .runtime_env import build_runtime_state
from .middleware.auth import login_required, current_user
from app.web.base import (
    main_bp,
    logger,
    Hasher,
    write_audit,
    purge_expired_trips,
    get_expired_trips,
    anonymize_employee,
    create_dsar_export,
    delete_employee_data,
    rectify_employee_name,
    export_trips_csv,
    export_employee_report_pdf,
    export_all_employees_report_pdf,
    presence_days,
    days_used_in_window,
    earliest_safe_entry,
    calculate_days_remaining,
    get_risk_level,
    days_until_compliant,
    validate_trip,
    validate_date_range,
    calculate_future_job_compliance,
    get_all_future_jobs_for_employee,
    calculate_what_if_scenario,
    get_risk_level_for_forecast,
    create_backup,
    auto_backup_if_needed,
    list_backups,
    LOGIN_ATTEMPTS,
    MAX_ATTEMPTS,
    ATTEMPT_WINDOW_SECONDS,
    redact_private_trip_data,
    get_db,
    current_actor,
    verify_and_upgrade_password,
    allowed_file,
)
import app.web.pages  # noqa: E402,F401
import app.web.privacy  # noqa: E402,F401

# Load environment variables
load_dotenv()

@main_bp.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

@main_bp.route('/api/version')
def api_version():
    from flask import current_app
    version = current_app.config.get('APP_VERSION', None)
    try:
        from app import APP_VERSION as defined_version
        version = version or defined_version
    except Exception:
        pass
    return jsonify({'version': version}), 200

# Error handlers now live in app/web/error_handlers.py (imported for side-effects)
