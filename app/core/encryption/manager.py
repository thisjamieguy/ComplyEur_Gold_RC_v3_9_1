"""
AES-256-GCM Encryption Manager
Provides authenticated encryption for PII fields
"""

import os
import base64
from typing import Optional, Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from .keys import KeyManager


class EncryptionManager:
    """
    Enterprise AES-256-GCM encryption manager.
    
    Features:
    - AES-256-GCM (authenticated encryption)
    - Unique IV per record
    - Automatic key management
    - Base64 encoding for database storage
    """
    
    IV_SIZE = 12  # 96 bits for GCM (recommended)
    TAG_SIZE = 16  # 128 bits authentication tag
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize encryption manager.
        
        Args:
            key: Optional encryption key (defaults to KeyManager.get_encryption_key())
        """
        self.key = key or KeyManager.get_encryption_key()
        if len(self.key) != 32:
            raise ValueError("Encryption key must be 32 bytes (256 bits)")
        
        self.cipher = AESGCM(self.key)
    
    def encrypt(self, plaintext: str, associated_data: Optional[bytes] = None) -> str:
        """
        Encrypt plaintext using AES-256-GCM.
        
        Args:
            plaintext: String to encrypt
            associated_data: Optional associated data for authentication
        
        Returns:
            Base64-encoded string: IV (12 bytes) + ciphertext + tag (16 bytes)
        """
        if not plaintext:
            return ""
        
        # Generate unique IV for this encryption
        import secrets
        iv = secrets.token_bytes(self.IV_SIZE)
        
        # Encrypt
        plaintext_bytes = plaintext.encode('utf-8')
        ciphertext = self.cipher.encrypt(iv, plaintext_bytes, associated_data)
        
        # Combine IV + ciphertext (which includes tag)
        encrypted_data = iv + ciphertext
        
        # Base64 encode for database storage
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    def decrypt(self, encrypted_data: str, associated_data: Optional[bytes] = None) -> str:
        """
        Decrypt ciphertext encrypted with AES-256-GCM.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            associated_data: Optional associated data (must match encryption)
        
        Returns:
            Decrypted plaintext string
        
        Raises:
            ValueError: If decryption fails (invalid key, corrupted data, etc.)
        """
        if not encrypted_data:
            return ""
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            if len(encrypted_bytes) < self.IV_SIZE + self.TAG_SIZE:
                raise ValueError("Encrypted data too short")
            
            # Extract IV and ciphertext
            iv = encrypted_bytes[:self.IV_SIZE]
            ciphertext = encrypted_bytes[self.IV_SIZE:]
            
            # Decrypt
            plaintext_bytes = self.cipher.decrypt(iv, ciphertext, associated_data)
            
            return plaintext_bytes.decode('utf-8')
        
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def re_encrypt(self, old_encrypted: str, old_key: bytes, associated_data: Optional[bytes] = None) -> str:
        """
        Re-encrypt data with a new key (for key rotation).
        
        Args:
            old_encrypted: Previously encrypted data
            old_key: Previous encryption key
            associated_data: Optional associated data
        
        Returns:
            New encrypted data with current key
        """
        # Decrypt with old key
        old_manager = EncryptionManager(old_key)
        plaintext = old_manager.decrypt(old_encrypted, associated_data)
        
        # Encrypt with new key
        return self.encrypt(plaintext, associated_data)
    
    @staticmethod
    def is_encrypted(possibly_encrypted: str) -> bool:
        """
        Check if a string appears to be encrypted (heuristic).
        
        Args:
            possibly_encrypted: String to check
        
        Returns:
            True if string appears encrypted (base64 format, minimum length)
        """
        if not possibly_encrypted:
            return False
        
        # Check if base64-encoded and has minimum length for IV + tag
        try:
            decoded = base64.b64decode(possibly_encrypted)
            # Minimum: IV (12) + tag (16) = 28 bytes
            return len(decoded) >= 28
        except Exception:
            return False

