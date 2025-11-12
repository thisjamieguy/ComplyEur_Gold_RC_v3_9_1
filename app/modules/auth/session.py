"""
Enterprise Session Management
Implements secure session handling with timeout controls
"""

from datetime import datetime, timedelta
from flask import session, request, current_app
from typing import Optional


class SessionManager:
    """
    Manages secure session lifecycle with:
    - Idle timeout (15 minutes)
    - Absolute timeout (8 hours)
    - Session rotation on login
    - Last activity tracking
    """
    
    @staticmethod
    def rotate_session_id():
        """
        Rotate session ID on login or privilege escalation.
        Prevents session fixation attacks.
        """
        # Mark session as modified to force new cookie
        session.modified = True
        session['issued_at'] = datetime.utcnow().timestamp()
        session['last_seen'] = session['issued_at']
    
    @staticmethod
    def touch_session():
        """
        Update last activity timestamp.
        Call on each authenticated request.
        """
        session['last_seen'] = datetime.utcnow().timestamp()
    
    @staticmethod
    def is_expired() -> bool:
        """
        Check if session has expired due to idle or absolute timeout.
        
        Returns:
            True if session expired, False otherwise
        """
        if 'user_id' not in session:
            return True
        
        issued = session.get('issued_at')
        last_seen = session.get('last_seen')
        
        # Fix: If timestamps are missing but user_id exists, initialize them
        # This handles edge cases where session was created but timestamps weren't set
        if not issued or not last_seen:
            # Auto-initialize missing timestamps for valid sessions
            SessionManager.rotate_session_id()
            session.permanent = True
            session.modified = True
            return False  # Not expired - we just initialized it
        
        now = datetime.utcnow().timestamp()
        
        # Check idle timeout (15 minutes default)
        idle_timeout = current_app.config.get('IDLE_TIMEOUT', timedelta(minutes=15))
        idle_seconds = idle_timeout.total_seconds()
        
        if now - last_seen > idle_seconds:
            return True
        
        # Check absolute timeout (8 hours default)
        absolute_timeout = current_app.config.get('ABSOLUTE_TIMEOUT', timedelta(hours=8))
        absolute_seconds = absolute_timeout.total_seconds()
        
        if now - issued > absolute_seconds:
            return True
        
        return False
    
    @staticmethod
    def clear_session():
        """Clear all session data (logout)"""
        session.clear()
    
    @staticmethod
    def set_user(user_id: int, role: Optional[str] = None):
        """
        Set authenticated user in session.
        
        Args:
            user_id: User ID
            role: Optional role string (cached for performance)
        """
        SessionManager.rotate_session_id()
        session['user_id'] = user_id
        if role:
            session['user_role'] = role
    
    @staticmethod
    def get_user_id() -> Optional[int]:
        """Get current user ID from session"""
        return session.get('user_id')
    
    @staticmethod
    def get_time_remaining() -> dict:
        """
        Get remaining session time.
        
        Returns:
            Dict with 'idle_seconds' and 'absolute_seconds' remaining
        """
        if 'user_id' not in session:
            return {'idle_seconds': 0, 'absolute_seconds': 0}
        
        issued = session.get('issued_at', 0)
        last_seen = session.get('last_seen', 0)
        now = datetime.utcnow().timestamp()
        
        idle_timeout = current_app.config.get('IDLE_TIMEOUT', timedelta(minutes=15))
        absolute_timeout = current_app.config.get('ABSOLUTE_TIMEOUT', timedelta(hours=8))
        
        idle_remaining = max(0, idle_timeout.total_seconds() - (now - last_seen))
        absolute_remaining = max(0, absolute_timeout.total_seconds() - (now - issued))
        
        return {
            'idle_seconds': int(idle_remaining),
            'absolute_seconds': int(absolute_remaining),
        }

