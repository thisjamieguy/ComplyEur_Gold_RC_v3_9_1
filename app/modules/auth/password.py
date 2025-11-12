"""
Enterprise Password Management
Implements Argon2id with server-side pepper for defense-in-depth
"""

import os
import hashlib
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
from flask import current_app
from app.security import zxcvbn


def get_pepper() -> bytes:
    """
    Retrieve server-side pepper from environment.
    Pepper is never stored in database - adds defense-in-depth.
    
    Pepper should be:
    - Set via PEPPER environment variable (32+ byte hex string recommended)
    - Stored in Render Secrets or secure KMS in production
    - Different per environment (dev/staging/prod)
    """
    pepper_env = os.getenv('PEPPER', '')
    if not pepper_env:
        # Generate warning but allow dev/testing without pepper
        # In production, PEPPER must be set
        if current_app and current_app.config.get('ENV') == 'production':
            raise ValueError(
                "PEPPER environment variable must be set in production. "
                "Generate with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        # Dev fallback - DO NOT USE IN PRODUCTION
        return b'dev-pepper-not-for-production-' + os.urandom(8)
    
    # Pepper should be hex-encoded bytes
    try:
        return bytes.fromhex(pepper_env)
    except ValueError:
        # If not hex, treat as UTF-8 string (hash it for consistency)
        return hashlib.sha256(pepper_env.encode('utf-8')).digest()


class PasswordManager:
    """
    Enterprise password hashing and verification with:
    - Argon2id (memory-hard, resistant to GPU attacks)
    - Server-side pepper (defense-in-depth)
    - Unique salt per password (handled by Argon2)
    - Password strength validation (zxcvbn)
    """
    
    def __init__(self):
        """Initialize with Argon2id parameters from config"""
        config = current_app.config if current_app else {}
        self.hasher = PasswordHasher(
            time_cost=config.get('ARGON2_TIME', 3),
            memory_cost=config.get('ARGON2_MEMORY', 65536),
            parallelism=config.get('ARGON2_PARALLELISM', 2),
            # Use Argon2id variant (default in argon2-cffi)
        )
        self.min_length = config.get('PASSWORD_MIN_LENGTH', 12)
        self.min_entropy = config.get('PASSWORD_MIN_ENTROPY', 3)  # zxcvbn score 0-4
    
    def hash(self, password: str, enforce_policy: bool = True) -> str:
        """
        Hash password with Argon2id + server-side pepper.
        
        Args:
            password: Plain text password
            enforce_policy: If True, validate password strength
        
        Returns:
            Argon2id hash string (includes salt)
        
        Raises:
            ValueError: If password doesn't meet policy
        """
        if enforce_policy:
            self._validate_strength(password)
        
        # Apply server-side pepper before hashing
        peppered = self._apply_pepper(password)
        
        try:
            return self.hasher.hash(peppered)
        except HashingError as e:
            raise ValueError(f"Password hashing failed: {e}")
    
    def verify(self, stored_hash: str, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            stored_hash: Argon2id hash from database
            password: Plain text password to verify
        
        Returns:
            True if password matches, False otherwise
        """
        try:
            peppered = self._apply_pepper(password)
            self.hasher.verify(stored_hash, peppered)
            return True
        except VerifyMismatchError:
            return False
        except Exception:
            # Any other error (invalid hash format, etc.) = failure
            return False
    
    def needs_rehash(self, stored_hash: str) -> bool:
        """
        Check if stored hash needs upgrading (parameters changed).
        
        Args:
            stored_hash: Current Argon2id hash
        
        Returns:
            True if hash should be rehashed with current parameters
        """
        try:
            return self.hasher.check_needs_rehash(stored_hash)
        except Exception:
            # Invalid hash format = needs rehash
            return True
    
    def _apply_pepper(self, password: str) -> str:
        """
        Apply server-side pepper to password.
        Uses HMAC-SHA256 for secure keyed hashing.
        
        Args:
            password: Plain text password
        
        Returns:
            Peppered password string (hex-encoded for Argon2 compatibility)
        """
        import hmac
        pepper = get_pepper()
        # Use HMAC to prevent length extension attacks
        # Convert to hex string for Argon2 (which expects strings, not bytes)
        peppered_bytes = hmac.new(pepper, password.encode('utf-8'), hashlib.sha256).digest()
        return peppered_bytes.hex()
    
    def _validate_strength(self, password: str) -> None:
        """
        Validate password meets enterprise policy.
        
        Policy:
        - Minimum 12 characters
        - zxcvbn entropy score >= 3 (moderate strength)
        
        Args:
            password: Password to validate
        
        Raises:
            ValueError: If password doesn't meet policy
        """
        if len(password) < self.min_length:
            raise ValueError(
                f"Password must be at least {self.min_length} characters long. "
                f"Current length: {len(password)}"
            )
        
        # zxcvbn strength analysis
        result = zxcvbn(password)
        score = result.get('score', 0)
        
        if score < self.min_entropy:
            feedback = result.get('feedback', {})
            suggestions = feedback.get('suggestions', [])
            warning = feedback.get('warning', '')
            
            msg = f"Password strength too weak (score: {score}/4). "
            if warning:
                msg += f"{warning} "
            if suggestions:
                msg += f"Suggestions: {', '.join(suggestions[:2])}"
            
            raise ValueError(msg)
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.
        Useful for initial admin setup or password reset tokens.
        
        Args:
            length: Desired password length
        
        Returns:
            Secure random password string
        """
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
