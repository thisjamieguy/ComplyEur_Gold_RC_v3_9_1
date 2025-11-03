"""
Health Check and Monitoring Endpoints
Phase 4: Network & Infrastructure Security
"""

from flask import Blueprint, jsonify
from datetime import datetime
import os

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        JSON with service status
    """
    try:
        # Check database connectivity
        db_status = "healthy"
        db_error = None
        
        try:
            from app.models import get_db
            conn = get_db()
            conn.execute('SELECT 1')
            conn.close()
        except Exception as e:
            db_status = "unhealthy"
            db_error = str(e)
        
        # Check disk space (if persistent disk)
        disk_status = "healthy"
        disk_error = None
        
        try:
            import shutil
            disk_path = os.getenv('PERSISTENT_DIR', '/var/data')
            if os.path.exists(disk_path):
                stat = shutil.disk_usage(disk_path)
                free_percent = (stat.free / stat.total) * 100
                if free_percent < 10:
                    disk_status = "warning"
                    disk_error = f"Low disk space: {free_percent:.1f}% free"
        except Exception as e:
            disk_status = "unhealthy"
            disk_error = str(e)
        
        # Overall status
        overall_status = "healthy"
        if db_status == "unhealthy" or disk_status == "unhealthy":
            overall_status = "unhealthy"
        elif db_status == "warning" or disk_status == "warning":
            overall_status = "degraded"
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'service': 'eu-trip-tracker',
            'version': os.getenv('APP_VERSION', '1.7.0'),
            'checks': {
                'database': {
                    'status': db_status,
                    'error': db_error
                },
                'disk': {
                    'status': disk_status,
                    'error': disk_error
                }
            }
        }), 200 if overall_status == "healthy" else 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/health/ready')
def readiness_check():
    """
    Readiness probe (Kubernetes-style).
    Checks if service is ready to accept traffic.

    Returns:
        200 if ready, 503 if not ready
    """
    try:
        # Check database
        from app.models import get_db
        conn = get_db()
        conn.execute('SELECT 1')
        conn.close()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503


@health_bp.route('/health/live')
def liveness_check():
    """
    Liveness probe (Kubernetes-style).
    Checks if service is alive.
    
    Returns:
        200 if alive
    """
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

