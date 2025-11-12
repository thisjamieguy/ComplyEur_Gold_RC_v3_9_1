"""
Encrypted Backup System
Creates AES-256-GCM encrypted backups for GDPR compliance
"""

import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime
from app.core.encryption import EncryptionManager
from app.services.backup import create_backup, get_backup_dir


def create_encrypted_backup(database_path, reason='manual'):
    """
    Create an encrypted backup of the database.
    
    Args:
        database_path: Path to SQLite database
        reason: Backup reason ('manual', 'auto', 'daily', etc.)
    
    Returns:
        dict with success status and backup file path
    """
    try:
        # First create unencrypted backup
        backup_result = create_backup(database_path, reason=reason)
        if not backup_result['success']:
            return backup_result
        
        backup_path = Path(backup_result['backup_path'])
        
        # Read backup file
        with open(backup_path, 'rb') as f:
            backup_data = f.read()
        
        # Compress with gzip (optional, but reduces size)
        compressed_data = gzip.compress(backup_data, compresslevel=6)
        
        # Encrypt compressed data
        # Convert bytes to string for encryption (base64 encode first)
        import base64
        backup_data_str = base64.b64encode(compressed_data).decode('utf-8')
        
        enc_manager = EncryptionManager()
        encrypted_data = enc_manager.encrypt(backup_data_str)
        
        # Write encrypted backup (add .encrypted extension)
        encrypted_backup_path = backup_path.with_suffix('.db.encrypted')
        with open(encrypted_backup_path, 'w') as f:
            f.write(encrypted_data)
        
        # Remove unencrypted backup (security: don't store plaintext)
        backup_path.unlink()
        
        # Update result with encrypted backup info
        backup_result['backup_path'] = str(encrypted_backup_path)
        backup_result['backup_filename'] = encrypted_backup_path.name
        backup_result['encrypted'] = True
        backup_result['size_bytes'] = encrypted_backup_path.stat().st_size
        
        return backup_result
    
    except Exception as e:
        return {'success': False, 'error': f'Encrypted backup failed: {str(e)}'}


def restore_encrypted_backup(encrypted_backup_path, target_database_path):
    """
    Restore database from encrypted backup.
    
    Args:
        encrypted_backup_path: Path to encrypted backup file
        target_database_path: Path where database should be restored
    
    Returns:
        dict with success status
    """
    try:
        encrypted_path = Path(encrypted_backup_path)
        if not encrypted_path.exists():
            return {'success': False, 'error': 'Encrypted backup file not found'}
        
        # Read encrypted data
        with open(encrypted_path, 'r') as f:
            encrypted_data = f.read()
        
        # Decrypt
        enc_manager = EncryptionManager()
        decrypted_data_str = enc_manager.decrypt(encrypted_data)
        
        # Decode from base64 and decompress
        import base64
        compressed_data = base64.b64decode(decrypted_data_str)
        backup_data = gzip.decompress(compressed_data)
        
        # Write to target location
        with open(target_database_path, 'wb') as f:
            f.write(backup_data)
        
        # Verify restored database is valid
        import sqlite3
        try:
            conn = sqlite3.connect(target_database_path)
            conn.execute('SELECT 1')
            conn.close()
        except Exception as e:
            return {'success': False, 'error': f'Restored database is invalid: {str(e)}'}
        
        return {
            'success': True,
            'restored_to': target_database_path,
            'source_backup': encrypted_path.name
        }
    
    except Exception as e:
        return {'success': False, 'error': f'Restore failed: {str(e)}'}


def list_encrypted_backups():
    """
    List all encrypted backups.
    
    Returns:
        list of backup info dictionaries
    """
    try:
        backup_dir = get_backup_dir()
        encrypted_backups = sorted(
            backup_dir.glob('eu_tracker_backup_*.db.encrypted'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        backups = []
        for backup_file in encrypted_backups:
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'age_days': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days,
                'encrypted': True
            })
        
        return {'success': True, 'backups': backups, 'count': len(backups)}
    
    except Exception as e:
        return {'success': False, 'error': str(e), 'backups': [], 'count': 0}


def verify_backup_integrity(encrypted_backup_path):
    """
    Verify encrypted backup integrity and decryptability.
    
    Args:
        encrypted_backup_path: Path to encrypted backup
    
    Returns:
        dict with verification status
    """
    try:
        encrypted_path = Path(encrypted_backup_path)
        if not encrypted_path.exists():
            return {'success': False, 'error': 'Backup file not found'}
        
        # Read and try to decrypt
        with open(encrypted_path, 'r') as f:
            encrypted_data = f.read()
        
        enc_manager = EncryptionManager()
        decrypted_data_str = enc_manager.decrypt(encrypted_data)
        
        # Try to decompress
        import base64
        compressed_data = base64.b64decode(decrypted_data_str)
        backup_data = gzip.decompress(compressed_data)
        
        # Verify it's a valid SQLite database
        import sqlite3
        import tempfile
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            tmp.write(backup_data)
            tmp_path = tmp.name
        
        try:
            conn = sqlite3.connect(tmp_path)
            # Try to read a few tables
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            # Cleanup
            os.unlink(tmp_path)
            
            return {
                'success': True,
                'valid': True,
                'tables_found': len(tables),
                'backup_size_bytes': encrypted_path.stat().st_size
            }
        
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return {'success': False, 'error': f'Invalid database structure: {str(e)}'}
    
    except Exception as e:
        return {'success': False, 'error': f'Verification failed: {str(e)}'}

