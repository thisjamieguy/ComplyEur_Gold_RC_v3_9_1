"""
Health Check and Monitoring Endpoints
Phase 4: Network & Infrastructure Security
"""

import time
from flask import Blueprint, jsonify, current_app

health_bp = Blueprint('health', __name__)


def _base_health():
    """Generate base health response with status, uptime, and version."""
    uptime = time.time() - current_app.config.get("APP_START_TS", time.time())
    return {
        "status": "healthy",
        "uptime_seconds": int(uptime),
        "version": current_app.config.get("APP_VERSION", "unknown")
    }


@health_bp.route('/health')
def health_root():
    """Main health check endpoint."""
    return jsonify(_base_health()), 200


@health_bp.route('/health/live')
def health_live():
    """Liveness probe (Kubernetes-style)."""
    h = _base_health()
    h["check"] = "liveness"
    return jsonify(h), 200


@health_bp.route('/health/ready')
def health_ready():
    """Readiness probe (Kubernetes-style)."""
    h = _base_health()
    h["check"] = "readiness"
    return jsonify(h), 200


@health_bp.route('/healthz')
def healthz():
    """Alternative health check endpoint (Kubernetes-style)."""
    return jsonify(_base_health()), 200


@health_bp.route('/api/version')
def api_version():
    """API version endpoint."""
    return jsonify({"version": current_app.config.get("APP_VERSION", "unknown")}), 200

