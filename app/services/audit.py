"""
Legacy Audit Service (Backward Compatible)
Phase 5: Enhanced with Immutable Audit Trail support
"""

import os
import hashlib
from datetime import datetime
from typing import Optional
from flask import request


def _ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


def mask_identifier(identifier: str) -> str:
    if not identifier:
        return 'unknown'
    digest = hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:12]
    return f'user_{digest}'


def write_audit(log_path: str, action: str, admin_identifier: str, details: Optional[dict] = None,
               ip_address: Optional[str] = None, use_immutable: bool = True) -> None:
    """
    Write audit log entry.
    
    Args:
        log_path: Path to audit log file
        action: Action type
        admin_identifier: Admin identifier (will be masked)
        details: Additional details dict
        ip_address: Client IP address (auto-detected if not provided)
        use_immutable: Use immutable audit trail (default: True)
    """
    try:
        # Get IP address from request if available
        if ip_address is None:
            try:
                from flask import request
                ip_address = request.remote_addr or request.headers.get('X-Forwarded-For', '').split(',')[0]
            except Exception:
                ip_address = None
        
        # Use immutable audit trail if enabled
        if use_immutable:
            try:
                from app.services.logging.audit_trail import get_audit_trail
                audit_trail = get_audit_trail(log_path)
                
                # Get user agent
                user_agent = None
                try:
                    from flask import request
                    user_agent = request.headers.get('User-Agent')
                except Exception:
                    pass
                
                audit_trail.write(
                    action=action,
                    admin_identifier=admin_identifier,
                    details=details,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                return
            except Exception:
                # Fallback to legacy if immutable trail fails
                pass
        
        # Legacy audit log format (backward compatible)
        _ensure_parent(log_path)
        ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        masked = mask_identifier(admin_identifier)
        safe_details = {}
        if isinstance(details, dict):
            # copy without sensitive values
            for k, v in details.items():
                if v is None:
                    continue
                if any(x in k.lower() for x in ['password', 'secret', 'token']):
                    continue
                safe_details[k] = v
        line = {
            'ts': ts,
            'action': action,
            'admin': masked,
            'details': safe_details,
        }
        if ip_address:
            line['ip'] = ip_address
        
        with open(log_path, 'a') as f:
            import json
            f.write(json.dumps(line) + '\n')
    except Exception:
        # Never break main flow due to logging errors
        pass




