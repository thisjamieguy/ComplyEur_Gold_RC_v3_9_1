"""
CAPTCHA Integration
Supports Google reCAPTCHA v3 for bot prevention
"""

import os
from typing import Optional, Dict, Any
from flask import request, current_app
try:
    import requests
except ImportError:
    requests = None


class CaptchaManager:
    """
    Manages CAPTCHA verification.
    Supports Google reCAPTCHA v3 (invisible, score-based).
    """
    
    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
    
    @staticmethod
    def get_site_key() -> Optional[str]:
        """Get reCAPTCHA site key from environment"""
        return os.getenv('RECAPTCHA_SITE_KEY')
    
    @staticmethod
    def get_secret_key() -> Optional[str]:
        """Get reCAPTCHA secret key from environment"""
        return os.getenv('RECAPTCHA_SECRET_KEY')
    
    @staticmethod
    def is_enabled() -> bool:
        """Check if CAPTCHA is configured"""
        return bool(
            requests
            and CaptchaManager.get_site_key()
            and CaptchaManager.get_secret_key()
        )
    
    @staticmethod
    def verify(token: str, remote_ip: Optional[str] = None) -> Dict[str, Any]:
        """
        Verify reCAPTCHA token.
        
        Args:
            token: reCAPTCHA response token from client
            remote_ip: Optional user's IP address
        
        Returns:
            Dict with:
            - success: bool
            - score: float (0.0-1.0, only if success=True)
            - action: str (only if success=True)
            - error_codes: list (only if success=False)
        """
        secret_key = CaptchaManager.get_secret_key()
        if not secret_key:
            # CAPTCHA not configured - allow request (dev mode)
            if current_app and current_app.config.get('ENV') != 'production':
                return {'success': True, 'score': 1.0, 'action': 'submit'}
            return {'success': False, 'error_codes': ['missing_secret']}
        
        if not token:
            return {'success': False, 'error_codes': ['missing_input_response']}
        
        # Verify with Google
        data = {
            'secret': secret_key,
            'response': token,
        }
        
        if remote_ip:
            data['remoteip'] = remote_ip
        
        if not requests:
            if current_app:
                current_app.logger.warning("requests library not installed; CAPTCHA verification skipped")
            return {'success': False, 'error_codes': ['requests_missing']}
        
        try:
            response = requests.post(
                CaptchaManager.VERIFY_URL,
                data=data,
                timeout=5
            )
            result = response.json()
            
            return {
                'success': result.get('success', False),
                'score': result.get('score', 0.0),
                'action': result.get('action', ''),
                'error_codes': result.get('error-codes', []),
            }
        
        except Exception as e:
            current_app.logger.error(f"CAPTCHA verification error: {e}")
            return {
                'success': False,
                'error_codes': ['network_error'],
            }
    
    @staticmethod
    def is_human(score_threshold: float = 0.5) -> bool:
        """
        Check if current request is from a human.
        Verifies CAPTCHA token from request.
        
        Args:
            score_threshold: Minimum score to consider human (default 0.5)
        
        Returns:
            True if verified as human, False otherwise
        """
        if not CaptchaManager.is_enabled():
            # Not configured - allow (for dev/testing)
            return True
        
        token = request.form.get('g-recaptcha-response') or request.json.get('captcha_token') if request.is_json else None
        
        if not token:
            return False
        
        remote_ip = request.remote_addr
        result = CaptchaManager.verify(token, remote_ip)
        
        if not result.get('success'):
            return False
        
        score = result.get('score', 0.0)
        return score >= score_threshold
