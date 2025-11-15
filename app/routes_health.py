"""
Health Check and Monitoring Endpoints
Phase 4: Network & Infrastructure Security
"""

from flask import Blueprint, jsonify, current_app

from app.services.health_status import build_health_payload, get_version_payload

health_bp = Blueprint('health', __name__)


def _success(payload):
    """Return a standard JSON 200 response."""
    return jsonify(payload), 200


@health_bp.route('/health')
def health_root():
    """Main health check endpoint."""
    return _success(build_health_payload(current_app.config))


@health_bp.route('/health/live')
def health_live():
    """Liveness probe (Kubernetes-style)."""
    return _success(build_health_payload(current_app.config, check="liveness"))


@health_bp.route('/health/ready')
def health_ready():
    """Readiness probe (Kubernetes-style)."""
    return _success(build_health_payload(current_app.config, check="readiness"))


@health_bp.route('/healthz')
def healthz():
    """Alternative health check endpoint (Kubernetes-style)."""
    return _success(build_health_payload(current_app.config))


@health_bp.route('/api/version')
def api_version():
    """API version endpoint."""
    return _success(get_version_payload(current_app.config))

