"""
Phase 2: Data Protection & Encryption - Test Suite
Tests encryption, key management, backups, and data masking
"""

import pytest
import os
import tempfile
import base64
from app.core.encryption import EncryptionManager, KeyManager
from app.core.masking import DataMasking
from app.services.backup_encrypted import (
    create_encrypted_backup,
    restore_encrypted_backup,
    verify_backup_integrity
)


@pytest.fixture
def encryption_key():
    """Generate test encryption key"""
    key = KeyManager.generate_key()
    os.environ['ENCRYPTION_KEY'] = key
    yield key
    os.environ.pop('ENCRYPTION_KEY', None)


@pytest.fixture
def enc_manager(encryption_key):
    """Create encryption manager with test key"""
    return EncryptionManager()


class TestKeyManagement:
    """Test encryption key management"""
    
    def test_generate_key(self):
        """Test key generation"""
        key = KeyManager.generate_key()
        assert isinstance(key, str)
        assert len(base64.b64decode(key)) == 32  # 32 bytes = 256 bits
    
    def test_get_encryption_key(self, encryption_key):
        """Test key retrieval from environment"""
        key_bytes = KeyManager.get_encryption_key()
        assert isinstance(key_bytes, bytes)
        assert len(key_bytes) == 32
    
    def test_key_validation(self):
        """Test key validation"""
        # Too short key
        os.environ['ENCRYPTION_KEY'] = base64.b64encode(b'short').decode()
        with pytest.raises(ValueError, match="32 bytes"):
            KeyManager.get_encryption_key()
        
        # Valid key
        valid_key = base64.b64encode(b'a' * 32).decode()
        os.environ['ENCRYPTION_KEY'] = valid_key
        key_bytes = KeyManager.get_encryption_key()
        assert len(key_bytes) == 32


class TestEncryption:
    """Test AES-256-GCM encryption"""
    
    def test_encrypt_decrypt(self, enc_manager):
        """Test basic encryption and decryption"""
        plaintext = "Test PII Data: Passport AB123456"
        encrypted = enc_manager.encrypt(plaintext)
        
        assert encrypted != plaintext
        assert len(encrypted) > 0
        assert enc_manager.is_encrypted(encrypted)
        
        decrypted = enc_manager.decrypt(encrypted)
        assert decrypted == plaintext
    
    def test_unique_iv_per_encryption(self, enc_manager):
        """Test that each encryption uses unique IV"""
        plaintext = "Same plaintext"
        encrypted1 = enc_manager.encrypt(plaintext)
        encrypted2 = enc_manager.encrypt(plaintext)
        
        # Should produce different ciphertexts (due to unique IV)
        assert encrypted1 != encrypted2
        
        # But both should decrypt to same plaintext
        assert enc_manager.decrypt(encrypted1) == plaintext
        assert enc_manager.decrypt(encrypted2) == plaintext
    
    def test_encrypt_empty_string(self, enc_manager):
        """Test encryption of empty string"""
        encrypted = enc_manager.encrypt("")
        assert encrypted == ""
        
        decrypted = enc_manager.decrypt("")
        assert decrypted == ""
    
    def test_decrypt_invalid_data(self, enc_manager):
        """Test decryption of invalid data fails"""
        with pytest.raises(ValueError, match="Decryption failed"):
            enc_manager.decrypt("invalid-base64-data")
        
        # Too short data
        short_data = base64.b64encode(b'too short').decode()
        with pytest.raises(ValueError):
            enc_manager.decrypt(short_data)
    
    def test_is_encrypted_check(self, enc_manager):
        """Test encrypted data detection"""
        plaintext = "Not encrypted"
        assert not enc_manager.is_encrypted(plaintext)
        
        encrypted = enc_manager.encrypt(plaintext)
        assert enc_manager.is_encrypted(encrypted)


class TestDataMasking:
    """Test data masking utilities"""
    
    def test_mask_passport_number(self):
        """Test passport number masking"""
        passport = "AB12345678"
        masked = DataMasking.mask_passport_number(passport, visible_digits=3)
        assert masked == "*******678"
        assert len(masked) == len(passport)
    
    def test_mask_id_number(self):
        """Test ID number masking"""
        id_num = "1234567890"
        masked = DataMasking.mask_id_number(id_num, visible_digits=2)
        assert masked == "********90"
    
    def test_mask_email(self):
        """Test email masking"""
        email = "john.doe@example.com"
        masked = DataMasking.mask_email(email)
        assert masked.startswith("j***@")
        assert masked.endswith("@example.com")
    
    def test_mask_name(self):
        """Test name masking"""
        name = "John Doe"
        masked = DataMasking.mask_name(name)
        assert masked == "J*** D***"
    
    def test_mask_phone_number(self):
        """Test phone number masking"""
        phone = "+1-555-123-4567"
        masked = DataMasking.mask_phone_number(phone, visible_digits=4)
        assert masked.endswith("4567")


class TestEncryptedBackups:
    """Test encrypted backup functionality"""
    
    def test_create_encrypted_backup(self, encryption_key, tmp_path):
        """Test creating encrypted backup"""
        # Create test database
        import sqlite3
        test_db = tmp_path / "test.db"
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.execute("INSERT INTO test (data) VALUES ('test data')")
        conn.commit()
        conn.close()
        
        # Create encrypted backup
        result = create_encrypted_backup(str(test_db), reason='test')
        
        assert result['success']
        assert result['encrypted'] is True
        assert result['backup_path'].endswith('.encrypted')
        assert os.path.exists(result['backup_path'])
    
    def test_verify_backup_integrity(self, encryption_key, tmp_path):
        """Test backup integrity verification"""
        # Create test database and backup
        import sqlite3
        test_db = tmp_path / "test.db"
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.commit()
        conn.close()
        
        backup_result = create_encrypted_backup(str(test_db), reason='test')
        
        # Verify integrity
        verify_result = verify_backup_integrity(backup_result['backup_path'])
        
        assert verify_result['success']
        assert verify_result['valid'] is True
        assert verify_result['tables_found'] > 0
    
    def test_restore_encrypted_backup(self, encryption_key, tmp_path):
        """Test restoring from encrypted backup"""
        # Create test database
        import sqlite3
        test_db = tmp_path / "test.db"
        conn = sqlite3.connect(test_db)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, data TEXT)")
        conn.execute("INSERT INTO test (data) VALUES ('original data')")
        conn.commit()
        conn.close()
        
        # Create backup
        backup_result = create_encrypted_backup(str(test_db), reason='test')
        
        # Modify database
        conn = sqlite3.connect(test_db)
        conn.execute("DELETE FROM test")
        conn.commit()
        conn.close()
        
        # Restore from backup
        restore_result = restore_encrypted_backup(
            backup_result['backup_path'],
            str(test_db)
        )
        
        assert restore_result['success']
        
        # Verify data restored
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("SELECT data FROM test")
        data = cursor.fetchone()
        conn.close()
        
        assert data[0] == 'original data'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

