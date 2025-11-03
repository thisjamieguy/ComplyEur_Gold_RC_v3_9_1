"""
Encryption Key Management
Environment-based key management with support for Render Secrets / AWS KMS
"""

import os
import base64
import hashlib
from typing import Optional
from flask import current_app


class KeyManager:
    """
    Manages encryption keys from environment variables.
    Supports:
    - Render Secrets (via environment variables)
    - AWS KMS (future: via boto3)
    - Local development (fallback with warning)
    """
    
    KEY_ENV_VAR = 'ENCRYPTION_KEY'
    KEY_ID_ENV_VAR = 'ENCRYPTION_KEY_ID'
    
    @staticmethod
    def get_encryption_key() -> bytes:
        """
        Retrieve encryption key from environment.
        
        Priority:
        1. ENCRYPTION_KEY (base64-encoded 32-byte key)
        2. Generated from SECRET_KEY (development only, not recommended)
        
        Returns:
            32-byte encryption key for AES-256
        
        Raises:
            ValueError: If key cannot be retrieved and in production
        """
        # Try to get key from environment
        key_str = os.getenv(KeyManager.KEY_ENV_VAR)
        
        if key_str:
            try:
                # Decode base64-encoded key
                key_bytes = base64.b64decode(key_str)
                if len(key_bytes) != 32:
                    raise ValueError(
                        f"ENCRYPTION_KEY must be 32 bytes (256 bits) when base64-decoded. "
                        f"Got {len(key_bytes)} bytes."
                    )
                return key_bytes
            except Exception as e:
                raise ValueError(
                    f"Failed to decode ENCRYPTION_KEY. "
                    f"Key must be base64-encoded 32-byte value. Error: {e}"
                )
        
        # Fallback: Generate from SECRET_KEY (development only)
        is_production = (
            current_app and current_app.config.get('ENV') == 'production'
        ) if current_app else os.getenv('FLASK_ENV') == 'production'
        
        if is_production:
            raise ValueError(
                "ENCRYPTION_KEY environment variable must be set in production. "
                "Generate with: python -c \"import secrets; import base64; print(base64.b64encode(secrets.token_bytes(32)).decode())\""
            )
        
        # Development fallback - derive from SECRET_KEY
        secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-not-for-production')
        key_hash = hashlib.sha256(secret_key.encode('utf-8')).digest()
        
        # Log warning
        import warnings
        warnings.warn(
            "Using SECRET_KEY-derived encryption key. "
            "Set ENCRYPTION_KEY environment variable for production.",
            UserWarning
        )
        
        return key_hash
    
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key (for initial setup).
        
        Returns:
            Base64-encoded 32-byte key string
        """
        import secrets
        key_bytes = secrets.token_bytes(32)
        return base64.b64encode(key_bytes).decode('utf-8')
    
    @staticmethod
    def get_key_id() -> Optional[str]:
        """
        Get encryption key ID (for key rotation tracking).
        
        Returns:
            Key ID string or None if not set
        """
        return os.getenv(KeyManager.KEY_ID_ENV_VAR)
    
    @staticmethod
    def rotate_key() -> str:
        """
        Generate a new encryption key for rotation.
        Note: Old data encrypted with previous key will need re-encryption.
        
        Returns:
            Base64-encoded new key
        """
        new_key = KeyManager.generate_key()
        
        # Log rotation event
        if current_app:
            current_app.logger.warning(
                "ENCRYPTION_KEY rotation initiated. "
                "Existing encrypted data must be re-encrypted with new key."
            )
        
        return new_key

