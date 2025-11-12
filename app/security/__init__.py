"""
Application Security Module
Phase 3: Application Security & Input Validation

Enterprise input validation, sanitization, and security utilities.
"""

from .sanitization import InputSanitizer
from .validation import InputValidator
from .file_uploads import SecureFileUpload

# Import password and session functions from parent security.py file
# Use importlib to avoid circular import issues
import importlib.util
import os

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
security_file = os.path.join(parent_dir, 'security.py')
if os.path.exists(security_file):
    spec = importlib.util.spec_from_file_location("security_module", security_file)
    security_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(security_module)
    
    verify_password = security_module.verify_password
    hash_password = security_module.hash_password
    rotate_session_id = security_module.rotate_session_id
    session_expired = security_module.session_expired
    touch_session = security_module.touch_session
    zxcvbn = security_module.zxcvbn
else:
    # Fallback if security.py doesn't exist
    raise ImportError("Could not find app/security.py file")

__all__ = [
    'InputSanitizer',
    'InputValidator',
    'SecureFileUpload',
    'verify_password',
    'hash_password',
    'rotate_session_id',
    'session_expired',
    'touch_session',
    'zxcvbn',
]
