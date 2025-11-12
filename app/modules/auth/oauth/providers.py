"""
OAuth 2.0 Provider Implementations
Supports Google Workspace and Microsoft Entra ID
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from flask import current_app, url_for
try:
    import requests
except ImportError:
    requests = None


class OAuthProvider(ABC):
    """Base class for OAuth 2.0 providers"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        pass
    
    @abstractmethod
    def get_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        pass
    
    @abstractmethod
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user profile information from provider"""
        pass
    
    @abstractmethod
    def validate_token(self, access_token: str) -> bool:
        """Validate access token is still valid"""
        pass


class GoogleOAuthProvider(OAuthProvider):
    """Google Workspace OAuth 2.0 Provider"""
    
    AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    TOKEN_VALIDATION_URL = "https://www.googleapis.com/oauth2/v1/tokeninfo"
    
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    
    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen
        }
        
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
    
    def get_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not requests:
            raise RuntimeError("requests library is required for Google OAuth flows")
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        response = requests.post(self.TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user profile from Google"""
        if not requests:
            raise RuntimeError("requests library is required for Google OAuth flows")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, access_token: str) -> bool:
        """Validate Google access token"""
        if not requests:
            return False
        params = {"access_token": access_token}
        try:
            response = requests.get(
                self.TOKEN_VALIDATION_URL, params=params, timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                # Check if token is for our client
                return data.get("audience") == self.client_id
            return False
        except Exception:
            return False


class MicrosoftOAuthProvider(OAuthProvider):
    """Microsoft Entra ID (Azure AD) OAuth 2.0 Provider"""
    
    AUTHORIZATION_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
    TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    USERINFO_URL = "https://graph.microsoft.com/v1.0/me"
    
    SCOPES = [
        "openid",
        "profile",
        "email",
    ]
    
    def get_authorization_url(self, state: str) -> str:
        """Generate Microsoft OAuth authorization URL"""
        from urllib.parse import urlencode
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "prompt": "consent",
        }
        
        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"
    
    def get_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if not requests:
            raise RuntimeError("requests library is required for Microsoft OAuth flows")
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        response = requests.post(self.TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user profile from Microsoft Graph"""
        if not requests:
            raise RuntimeError("requests library is required for Microsoft OAuth flows")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.USERINFO_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def validate_token(self, access_token: str) -> bool:
        """Validate Microsoft access token by attempting to use it"""
        if not requests:
            return False
        try:
            # Try to fetch user info - if successful, token is valid
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                self.USERINFO_URL, headers=headers, timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
