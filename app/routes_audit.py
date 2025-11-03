"""
Audit Trail Dashboard
Phase 5: Compliance & Monitoring
Provides viewable audit trail with filtering and search
"""

from flask import Blueprint, render_template, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta, date
import os

audit_bp = Blueprint('audit', __name__)


def login_required(f):
    """Require login for audit access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


@audit_bp.route('/admin/audit-trail')
@login_required
def audit_trail_dashboard():
    """
    Audit trail dashboard page.
    Shows recent audit log entries with filtering.
    """
    try:
        from app.services.logging.audit_trail import get_audit_trail
        
        log_path = os.getenv('AUDIT_LOG_PATH', 'logs/audit.log')
        audit_trail = get_audit_trail(log_path)
        
        # Get recent entries (last 100)
        entries = audit_trail.get_entries(limit=100)
        
        # Verify integrity
        is_valid, errors = audit_trail.verify_integrity()
        
        return render_template('admin/audit_trail.html',
                             entries=entries,
                             integrity_valid=is_valid,
                             integrity_errors=errors,
                             total_entries=len(entries))
    
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"Failed to load audit trail: {e}")
        return render_template('admin/audit_trail.html',
                             entries=[],
                             integrity_valid=False,
                             integrity_errors=[str(e)],
                             total_entries=0)


@audit_bp.route('/api/audit-trail')
@login_required
def audit_trail_api():
    """
    Audit trail API endpoint.
    Returns JSON with filtered audit entries.
    """
    try:
        from app.services.logging.audit_trail import get_audit_trail
        
        log_path = os.getenv('AUDIT_LOG_PATH', 'logs/audit.log')
        audit_trail = get_audit_trail(log_path)
        
        # Get filters from query parameters
        action_filter = request.args.get('action')
        limit = request.args.get('limit', type=int)
        
        # Get entries
        entries = audit_trail.get_entries(action_filter=action_filter, limit=limit)
        
        # Verify integrity
        is_valid, errors = audit_trail.verify_integrity()
        
        return jsonify({
            'success': True,
            'entries': entries,
            'total': len(entries),
            'integrity': {
                'valid': is_valid,
                'errors': errors
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audit_bp.route('/api/audit-trail/stats')
@login_required
def audit_trail_stats():
    """
    Audit trail statistics API.
    Returns summary statistics about audit logs.
    """
    try:
        from app.services.logging.audit_trail import get_audit_trail
        
        log_path = os.getenv('AUDIT_LOG_PATH', 'logs/audit.log')
        audit_trail = get_audit_trail(log_path)
        
        # Get all entries (for statistics)
        entries = audit_trail.get_entries(limit=1000)
        
        # Calculate statistics
        total_entries = len(entries)
        
        # Count by action type
        action_counts = {}
        for entry in entries:
            action = entry.get('action', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Count by admin (masked)
        admin_counts = {}
        for entry in entries:
            admin = entry.get('admin', 'unknown')
            admin_counts[admin] = admin_counts.get(admin, 0) + 1
        
        # Recent activity (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(days=1)
        recent_entries = [
            e for e in entries
            if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00').replace('+00:00', '')) > cutoff
        ]
        
        # Verify integrity
        is_valid, errors = audit_trail.verify_integrity()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_entries': total_entries,
                'recent_24h': len(recent_entries),
                'action_counts': action_counts,
                'admin_counts': admin_counts,
                'integrity': {
                    'valid': is_valid,
                    'errors': len(errors)
                }
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@audit_bp.route('/api/log-integrity/check')
@login_required
def check_log_integrity():
    """
    Check log integrity endpoint.
    Runs integrity check on all log files.
    """
    try:
        from app.services.logging.integrity_checker import get_integrity_checker
        
        log_dir = os.getenv('LOG_DIR', 'logs')
        checker = get_integrity_checker(log_dir)
        
        # Check all logs
        results = checker.check_all_logs()
        
        # Store today's hashes
        today = date.today()
        for log_file in results.keys():
            checker.store_integrity_hash(log_file, today)
        
        # Summary
        valid_count = sum(1 for is_valid, _ in results.values() if is_valid)
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'summary': {
                'total_files': total_count,
                'valid_files': valid_count,
                'invalid_files': total_count - valid_count,
                'check_date': today.isoformat()
            },
            'results': {
                log_file: result for log_file, (is_valid, result) in results.items()
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

