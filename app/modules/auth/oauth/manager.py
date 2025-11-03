"""
OAuth 2.0 Manager
Handles OAuth flow and user provisioning
"""

import os
import secrets
from datetime import datetime
from typing import Optional, Dict, Any
from flask import session, url_for, current_app
from .providers import GoogleOAuthProvider, MicrosoftOAuthProvider


class OAuthManager:
    """
    Manages OAuth 2.0 authentication flows.
    Supports Google Workspace and Microsoft Entra ID.
    """
    
    @staticmethod
    def get_provider(provider_name: str) -> Optional[Any]:
        """
        Get configured OAuth provider.
        
        Args:
            provider_name: 'google' or 'microsoft'
        
        Returns:
            OAuthProvider instance or None if not configured
        """
        provider_name = provider_name.lower()
        
        if provider_name == 'google':
            client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
            client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                return None
            
            redirect_uri = url_for('auth.oauth_callback', provider='google', _external=True)
            return GoogleOAuthProvider(client_id, client_secret, redirect_uri)
        
        elif provider_name == 'microsoft':
            client_id = os.getenv('MICROSOFT_OAUTH_CLIENT_ID')
            client_secret = os.getenv('MICROSOFT_OAUTH_CLIENT_SECRET')
            
            if not client_id or not client_secret:
                return None
            
            redirect_uri = url_for('auth.oauth_callback', provider='microsoft', _external=True)
            return MicrosoftOAuthProvider(client_id, client_secret, redirect_uri)
        
        return None
    
    @staticmethod
    def initiate_login(provider_name: str) -> Optional[str]:
        """
        Initiate OAuth login flow.
        
        Args:
            provider_name: 'google' or 'microsoft'
        
        Returns:
            Authorization URL to redirect user to, or None if not configured
        """
        provider = OAuthManager.get_provider(provider_name)
        if not provider:
            return None
        
        # Generate CSRF state token
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        session['oauth_provider'] = provider_name
        
        return provider.get_authorization_url(state)
    
    @staticmethod
    def handle_callback(code: str, state: str) -> Optional[Dict[str, Any]]:
        """
        Handle OAuth callback and create/authenticate user.
        
        Args:
            code: Authorization code from provider
            state: CSRF state token
        
        Returns:
            Dict with 'user_id' and 'user_info', or None on failure
        """
        # Validate state token
        if state != session.get('oauth_state'):
            return None
        
        provider_name = session.get('oauth_provider')
        if not provider_name:
            return None
        
        provider = OAuthManager.get_provider(provider_name)
        if not provider:
            return None
        
        try:
            # Exchange code for token
            token_response = provider.get_token(code)
            access_token = token_response.get('access_token')
            
            if not access_token:
                return None
            
            # Get user info
            user_info = provider.get_user_info(access_token)
            
            # Create or update user in database
            from ...models_auth import User
            from ... import db
            
            email = user_info.get('email') or user_info.get('mail') or user_info.get('userPrincipalName')
            name = user_info.get('name') or user_info.get('displayName', email.split('@')[0])
            
            if not email:
                return None
            
            # Find or create user
            user = User.query.filter_by(username=email).first()
            
            if not user:
                # Create new user
                user = User(
                    username=email,
                    password_hash='',  # OAuth users don't need password
                    role='employee',  # Default role
                )
                db.session.add(user)
            
            # Update user info
            if hasattr(user, 'oauth_provider'):
                user.oauth_provider = provider_name
            if hasattr(user, 'oauth_id'):
                user.oauth_id = user_info.get('id') or user_info.get('sub')
            
            user.last_login_at = datetime.utcnow()
            db.session.commit()
            
            # Clear OAuth state
            session.pop('oauth_state', None)
            session.pop('oauth_provider', None)
            
            return {
                'user_id': user.id,
                'user_info': user_info,
            }
        
        except Exception as e:
            current_app.logger.error(f"OAuth callback error: {e}")
            return None
    
    @staticmethod
    def is_enabled(provider_name: str) -> bool:
        """Check if OAuth provider is configured"""
        return OAuthManager.get_provider(provider_name) is not None

