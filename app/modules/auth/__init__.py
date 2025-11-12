"""
ComplyEur - Enterprise Security Authentication Module
Phase 1: Authentication & Access Control

This module centralizes all authentication and authorization logic
for GDPR / ISO 27001 / NIS2 compliance.
"""

from .password import PasswordManager, get_pepper
from .rbac import Role, Permission, require_permission, require_role
from .session import SessionManager
from .oauth import OAuthManager
from .captcha import CaptchaManager

__all__ = [
    'PasswordManager',
    'get_pepper',
    'Role',
    'Permission',
    'require_permission',
    'require_role',
    'SessionManager',
    'OAuthManager',
    'CaptchaManager',
]

