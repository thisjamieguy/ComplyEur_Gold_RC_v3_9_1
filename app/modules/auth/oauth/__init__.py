"""
OAuth 2.0 + OpenID Connect Support
Supports Google Workspace and Microsoft Entra ID
"""

from .providers import OAuthProvider, GoogleOAuthProvider, MicrosoftOAuthProvider
from .manager import OAuthManager

__all__ = [
    'OAuthProvider',
    'GoogleOAuthProvider',
    'MicrosoftOAuthProvider',
    'OAuthManager',
]

