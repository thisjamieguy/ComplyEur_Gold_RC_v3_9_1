"""
Session Manager Tests
Tests session management functionality including timeouts and consistency.
"""

import pytest
import time
from datetime import datetime, timedelta
from flask import session
from app.modules.auth.session import SessionManager


def test_session_rotation(test_app):
    """Test that session ID is rotated on login"""
    with test_app.app_context():
        with test_app.test_request_context():
            # Set initial user
            SessionManager.set_user(1, 'admin')
            initial_issued = session.get('issued_at')
            
            # Rotate session
            SessionManager.rotate_session_id()
            rotated_issued = session.get('issued_at')
            
            assert rotated_issued != initial_issued, "Session ID should be rotated"
            assert session.get('user_id') == 1, "User ID should persist"


def test_session_touch(test_app):
    """Test that session activity is updated"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            initial_last_seen = session.get('last_seen')
            
            # Wait a bit
            time.sleep(0.1)
            
            # Touch session
            SessionManager.touch_session()
            updated_last_seen = session.get('last_seen')
            
            assert updated_last_seen > initial_last_seen, "Last seen should be updated"


def test_session_expiration_idle(test_app):
    """Test that session expires after idle timeout"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            # Set last_seen to past (simulate idle)
            session['last_seen'] = datetime.utcnow().timestamp() - (16 * 60)  # 16 minutes ago
            
            # Check if expired
            assert SessionManager.is_expired(), "Session should be expired after idle timeout"


def test_session_expiration_absolute(test_app):
    """Test that session expires after absolute timeout"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            # Set issued_at to past (simulate absolute timeout)
            session['issued_at'] = datetime.utcnow().timestamp() - (9 * 60 * 60)  # 9 hours ago
            
            # Check if expired
            assert SessionManager.is_expired(), "Session should be expired after absolute timeout"


def test_session_not_expired(test_app):
    """Test that session is not expired within limits"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            # Session should not be expired immediately
            assert not SessionManager.is_expired(), "Session should not be expired immediately"


def test_session_clear(test_app):
    """Test that session is cleared on logout"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            assert session.get('user_id') == 1, "User ID should be set"
            
            # Clear session
            SessionManager.clear_session()
            
            assert session.get('user_id') is None, "User ID should be cleared"


def test_session_time_remaining(test_app):
    """Test that session time remaining is calculated correctly"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            # Get time remaining
            time_remaining = SessionManager.get_time_remaining()
            
            assert 'idle_seconds' in time_remaining, "Should return idle_seconds"
            assert 'absolute_seconds' in time_remaining, "Should return absolute_seconds"
            assert time_remaining['idle_seconds'] > 0, "Idle seconds should be positive"
            assert time_remaining['absolute_seconds'] > 0, "Absolute seconds should be positive"


def test_session_auto_initialize(test_app):
    """Test that missing session timestamps are auto-initialized"""
    with test_app.app_context():
        with test_app.test_request_context():
            # Set user_id without timestamps (simulate edge case)
            session['user_id'] = 1
            session.pop('issued_at', None)
            session.pop('last_seen', None)
            
            # Check if expired (should auto-initialize)
            expired = SessionManager.is_expired()
            
            # Should not be expired (auto-initialized)
            assert not expired, "Session should not be expired after auto-initialization"
            assert session.get('issued_at') is not None, "Issued timestamp should be set"
            assert session.get('last_seen') is not None, "Last seen timestamp should be set"


def test_session_get_user_id(test_app):
    """Test that user ID can be retrieved from session"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            user_id = SessionManager.get_user_id()
            
            assert user_id == 1, "Should return user ID"


def test_session_set_user(test_app):
    """Test that user is set in session with role"""
    with test_app.app_context():
        with test_app.test_request_context():
            SessionManager.set_user(1, 'admin')
            
            assert session.get('user_id') == 1, "User ID should be set"
            assert session.get('user_role') == 'admin', "User role should be set"
            assert session.get('issued_at') is not None, "Issued timestamp should be set"
            assert session.get('last_seen') is not None, "Last seen timestamp should be set"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

