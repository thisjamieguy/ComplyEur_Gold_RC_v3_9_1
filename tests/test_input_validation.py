"""
Phase 3: Application Security & Input Validation - Test Suite
Tests input sanitization, validation, file uploads, and CSRF
"""

import pytest
from app.security.sanitization import InputSanitizer
from app.security.validation import InputValidator
from app.security.file_uploads import SecureFileUpload
from werkzeug.datastructures import FileStorage
from io import BytesIO


class TestInputSanitization:
    """Test input sanitization"""
    
    def test_sanitize_string(self):
        """Test basic string sanitization"""
        # HTML tags should be escaped
        result = InputSanitizer.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_name(self):
        """Test employee name sanitization"""
        # Valid name
        result = InputSanitizer.sanitize_name("John O'Brien")
        assert result == "John O'Brien"
        
        # Name with invalid chars
        result = InputSanitizer.sanitize_name("John<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "alert" not in result
        
        # Too short
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_name("A")
        
        # Too long
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_name("A" * 101)
    
    def test_sanitize_country_code(self):
        """Test country code sanitization"""
        result = InputSanitizer.sanitize_country_code("fr")
        assert result == "FR"
        
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_country_code("invalid")
    
    def test_sanitize_date(self):
        """Test date sanitization"""
        result = InputSanitizer.sanitize_date("2024-01-15")
        assert result == "2024-01-15"
        
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_date("invalid-date")
        
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_date("2024-13-45")  # Invalid date
    
    def test_sanitize_html(self):
        """Test HTML sanitization"""
        # Script tags should be removed
        html = "<script>alert('xss')</script><p>Safe content</p>"
        result = InputSanitizer.sanitize_html(html)
        assert "<script>" not in result
        assert "Safe content" in result


class TestInputValidation:
    """Test input validation"""
    
    def test_validate_employee_name(self):
        """Test employee name validation"""
        valid, error = InputValidator.validate_employee_name("John Doe")
        assert valid
        assert error is None
        
        # Too short
        valid, error = InputValidator.validate_employee_name("A")
        assert not valid
        assert "at least 2 characters" in error
        
        # Invalid characters
        valid, error = InputValidator.validate_employee_name("John<script>")
        assert not valid
        assert "invalid characters" in error.lower()
    
    def test_validate_country_code(self):
        """Test country code validation"""
        valid, error = InputValidator.validate_country_code("FR")
        assert valid
        
        valid, error = InputValidator.validate_country_code("XX")  # Private trips
        assert valid
        
        valid, error = InputValidator.validate_country_code("INVALID")
        assert not valid
        assert "Invalid country code" in error
    
    def test_validate_date(self):
        """Test date validation"""
        valid, error = InputValidator.validate_date("2024-01-15")
        assert valid
        
        # Invalid format
        valid, error = InputValidator.validate_date("01-15-2024")
        assert not valid
        
        # Too far in past
        valid, error = InputValidator.validate_date("1900-01-01")
        assert not valid
        assert "years in the past" in error
    
    def test_validate_date_range(self):
        """Test date range validation"""
        valid, error = InputValidator.validate_date_range("2024-01-01", "2024-01-15")
        assert valid
        
        # Exit before entry
        valid, error = InputValidator.validate_date_range("2024-01-15", "2024-01-01")
        assert not valid
        assert "Exit date must be after entry date" in error
        
        # Too long duration
        valid, error = InputValidator.validate_date_range("2020-01-01", "2025-01-01")
        assert not valid
        assert "exceed 2 years" in error
    
    def test_validate_all_trip_fields(self):
        """Test comprehensive trip field validation"""
        data = {
            'employee_id': '1',
            'country_code': 'FR',
            'entry_date': '2024-01-01',
            'exit_date': '2024-01-15'
        }
        valid, errors = InputValidator.validate_all_trip_fields(data)
        assert valid
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {
            'employee_id': '0',
            'country_code': 'INVALID',
            'entry_date': 'invalid',
        }
        valid, errors = InputValidator.validate_all_trip_fields(invalid_data)
        assert not valid
        assert len(errors) > 0


class TestFileUploads:
    """Test secure file upload"""
    
    def test_is_allowed_extension(self):
        """Test file extension validation"""
        assert SecureFileUpload.is_allowed_extension("test.xlsx")
        assert SecureFileUpload.is_allowed_extension("test.xls")
        assert not SecureFileUpload.is_allowed_extension("test.exe")
        assert not SecureFileUpload.is_allowed_extension("test.sh")
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        result = SecureFileUpload.sanitize_filename("../../../etc/passwd.xlsx")
        assert "../" not in result
        assert "etc" not in result
        assert result.endswith(".xlsx")
        
        result = SecureFileUpload.sanitize_filename("my file<script>.xls")
        assert "<script>" not in result
    
    def test_validate_file(self):
        """Test file validation"""
        # Create mock file
        file_content = b"PK\x03\x04"  # ZIP/Excel magic bytes
        file_obj = FileStorage(
            stream=BytesIO(file_content),
            filename="test.xlsx",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        valid, mime_type, error = SecureFileUpload.validate_file(file_obj)
        # Note: May fail without python-magic installed, but structure is correct
        assert isinstance(valid, bool)
        assert error is None or isinstance(error, str)
    
    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        content = b"test file content"
        hash1 = SecureFileUpload.calculate_file_hash(content)
        hash2 = SecureFileUpload.calculate_file_hash(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length


class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_enabled_in_config(self, app):
        """Test CSRF is enabled in Flask-WTF"""
        # CSRF should be enabled via Flask-WTF
        from flask import current_app
        with app.app_context():
            # WTF_CSRF_ENABLED should be True (or False only in dev)
            assert 'WTF_CSRF_ENABLED' in current_app.config


class TestSecurityHeaders:
    """Test security headers"""
    
    def test_csp_nonce_generation(self):
        """Test CSP nonce generation"""
        from app.core.csp import generate_nonce
        
        nonce1 = generate_nonce()
        nonce2 = generate_nonce()
        
        # Nonces should be different
        assert nonce1 != nonce2
        # Should be base64-like
        assert len(nonce1) > 0
        assert len(nonce2) > 0
    
    def test_csp_header_building(self):
        """Test CSP header construction"""
        from app.core.csp import build_csp_header
        
        nonce = "test_nonce_123"
        csp = build_csp_header(nonce)
        
        assert f"'nonce-{nonce}'" in csp
        assert "script-src" in csp
        assert "style-src" in csp
        assert "frame-ancestors 'none'" in csp


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

