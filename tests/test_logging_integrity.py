"""
Phase 5: Logging Integrity Tests
Tests for immutable audit trail and log integrity checking
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import date

from app.services.logging.audit_trail import ImmutableAuditTrail
from app.services.logging.integrity_checker import LogIntegrityChecker


@pytest.fixture
def temp_log_dir():
    """Create temporary log directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def audit_trail(temp_log_dir):
    """Create audit trail instance"""
    log_path = os.path.join(temp_log_dir, 'audit.log')
    return ImmutableAuditTrail(log_path)


@pytest.fixture
def integrity_checker(temp_log_dir):
    """Create integrity checker instance"""
    return LogIntegrityChecker(temp_log_dir)


class TestImmutableAuditTrail:
    """Test immutable audit trail"""
    
    def test_write_entry(self, audit_trail):
        """Test writing audit log entry"""
        success = audit_trail.write(
            action='login',
            admin_identifier='test_admin',
            details={'ip': '127.0.0.1'},
            ip_address='127.0.0.1'
        )
        assert success
        
        # Verify file exists
        assert audit_trail.log_path.exists()
        assert audit_trail.integrity_file.exists()
    
    def test_hash_chain(self, audit_trail):
        """Test hash chain integrity"""
        # Write multiple entries
        audit_trail.write(action='login', admin_identifier='admin1')
        audit_trail.write(action='logout', admin_identifier='admin1')
        audit_trail.write(action='export', admin_identifier='admin1')
        
        # Verify integrity
        is_valid, errors = audit_trail.verify_integrity()
        assert is_valid
        assert len(errors) == 0
    
    def test_entry_retrieval(self, audit_trail):
        """Test retrieving audit entries"""
        audit_trail.write(action='login', admin_identifier='admin1')
        audit_trail.write(action='export', admin_identifier='admin2')
        
        entries = audit_trail.get_entries()
        assert len(entries) == 2
        assert entries[0]['action'] == 'export'  # Newest first
        assert entries[1]['action'] == 'login'
    
    def test_entry_filtering(self, audit_trail):
        """Test filtering entries by action"""
        audit_trail.write(action='login', admin_identifier='admin1')
        audit_trail.write(action='export', admin_identifier='admin1')
        audit_trail.write(action='login', admin_identifier='admin2')
        
        login_entries = audit_trail.get_entries(action_filter='login')
        assert len(login_entries) == 2
        
        export_entries = audit_trail.get_entries(action_filter='export')
        assert len(export_entries) == 1
    
    def test_admin_masking(self, audit_trail):
        """Test admin identifier masking"""
        audit_trail.write(action='login', admin_identifier='sensitive_admin_name')
        
        entries = audit_trail.get_entries()
        assert len(entries) == 1
        assert entries[0]['admin'].startswith('user_')
        assert 'sensitive_admin_name' not in entries[0]['admin']
    
    def test_sensitive_data_removal(self, audit_trail):
        """Test removal of sensitive data from details"""
        audit_trail.write(
            action='login',
            admin_identifier='admin',
            details={
                'password': 'secret123',
                'api_key': 'key123',
                'token': 'token123',
                'safe_field': 'safe_value'
            }
        )
        
        entries = audit_trail.get_entries()
        assert len(entries) == 1
        details = entries[0]['details']
        assert 'password' not in details
        assert 'api_key' not in details
        assert 'token' not in details
        assert 'safe_field' in details
        assert details['safe_field'] == 'safe_value'


class TestLogIntegrityChecker:
    """Test log integrity checker"""
    
    def test_calculate_file_hash(self, integrity_checker, temp_log_dir):
        """Test file hash calculation"""
        test_file = Path(temp_log_dir) / 'test.log'
        test_file.write_text('test content\n')
        
        hash1 = integrity_checker.calculate_file_hash(test_file)
        hash2 = integrity_checker.calculate_file_hash(test_file)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_store_integrity_hash(self, integrity_checker, temp_log_dir):
        """Test storing integrity hash"""
        test_file = Path(temp_log_dir) / 'audit.log'
        test_file.write_text('log entry 1\n')
        
        success = integrity_checker.store_integrity_hash('audit.log')
        assert success
        
        # Verify integrity file created
        integrity_file = integrity_checker.integrity_dir / f"audit.log.{date.today().isoformat()}.hash"
        assert integrity_file.exists()
        
        # Verify hash stored
        with open(integrity_file) as f:
            data = json.load(f)
            assert 'hash' in data
            assert 'date' in data
    
    def test_check_log_integrity_valid(self, integrity_checker, temp_log_dir):
        """Test integrity check on valid log"""
        test_file = Path(temp_log_dir) / 'audit.log'
        test_file.write_text('log entry\n')
        
        # Store hash
        integrity_checker.store_integrity_hash('audit.log')
        
        # Check integrity
        is_valid, result = integrity_checker.check_log_integrity('audit.log')
        assert is_valid
        assert result['status'] == 'valid'
    
    def test_check_log_integrity_tampered(self, integrity_checker, temp_log_dir):
        """Test integrity check on tampered log"""
        test_file = Path(temp_log_dir) / 'audit.log'
        test_file.write_text('original log\n')
        
        # Store hash
        integrity_checker.store_integrity_hash('audit.log')
        
        # Tamper with file
        test_file.write_text('tampered log\n')
        
        # Check integrity (should detect tampering)
        is_valid, result = integrity_checker.check_log_integrity('audit.log')
        assert not is_valid
        assert result['status'] == 'tampered'
        assert 'warning' in result
    
    def test_daily_integrity_check(self, integrity_checker, temp_log_dir):
        """Test daily integrity check for all logs"""
        # Create test log files
        (Path(temp_log_dir) / 'audit.log').write_text('audit log\n')
        (Path(temp_log_dir) / 'app.log').write_text('app log\n')
        
        # Run daily check
        summary = integrity_checker.daily_integrity_check()
        
        assert 'date' in summary
        assert 'total_files' in summary
        assert 'valid_files' in summary
        assert summary['total_files'] >= 2
        assert 'checks' in summary


class TestIntegration:
    """Integration tests"""
    
    def test_audit_trail_with_integrity_check(self, temp_log_dir):
        """Test audit trail with integrity checking"""
        log_path = os.path.join(temp_log_dir, 'audit.log')
        audit_trail = ImmutableAuditTrail(log_path)
        integrity_checker = LogIntegrityChecker(temp_log_dir)
        
        # Write entries
        audit_trail.write(action='login', admin_identifier='admin1')
        audit_trail.write(action='export', admin_identifier='admin1')
        
        # Verify audit trail integrity
        is_valid, errors = audit_trail.verify_integrity()
        assert is_valid
        
        # Check log file integrity
        is_valid, result = integrity_checker.check_log_integrity('audit.log')
        # First check should be 'new' status
        assert result['status'] in ('new', 'valid')
        
        # Store hash and check again
        integrity_checker.store_integrity_hash('audit.log')
        is_valid, result = integrity_checker.check_log_integrity('audit.log')
        assert is_valid


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

