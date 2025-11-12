"""
Secure File Upload Handler
MIME type checking and validation for file uploads
"""

import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List
from werkzeug.utils import secure_filename
from flask import current_app


class SecureFileUpload:
    """
    Secure file upload handler with:
    - MIME type validation
    - File extension whitelist
    - Size limits
    - Filename sanitization
    - Content scanning (basic)
    """
    
    # Allowed file extensions (whitelist)
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf'}
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
        'text/csv',
        'application/pdf',
        'application/octet-stream',  # Sometimes Excel files are detected as this
    }
    
    # Maximum file size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
    
    @staticmethod
    def is_allowed_extension(filename: str) -> bool:
        """
        Check if file extension is allowed.
        
        Args:
            filename: File name
        
        Returns:
            True if extension is allowed
        """
        if not filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return ext in SecureFileUpload.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_file_mime_type(file_content: bytes, filename: str) -> str:
        """
        Get MIME type from file content (magic bytes).
        
        Args:
            file_content: File content bytes
            filename: File name (for fallback)
        
        Returns:
            MIME type string
        """
        # Try python-magic first (most accurate)
        # Note: Requires libmagic system library (apt-get install libmagic1 / brew install libmagic)
        try:
            import magic
            mime = magic.Magic(mime=True)
            mime_type = mime.from_buffer(file_content[:1024])  # Read first 1KB
            if mime_type:
                return mime_type
        except (ImportError, Exception):
            # python-magic not available or libmagic not installed
            pass
        
        # Fallback: check file extension
        if filename.lower().endswith('.xlsx'):
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif filename.lower().endswith('.xls'):
            return 'application/vnd.ms-excel'
        elif filename.lower().endswith('.csv'):
            return 'text/csv'
        elif filename.lower().endswith('.pdf'):
            return 'application/pdf'
        
        return 'application/octet-stream'
    
    @staticmethod
    def validate_file(file, filename: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate uploaded file.
        
        Args:
            file: File object from Flask request
            filename: Optional filename (if not in file object)
        
        Returns:
            Tuple of (is_valid, mime_type, error_message)
        """
        if not file:
            return False, None, "No file provided"
        
        filename = filename or (file.filename if hasattr(file, 'filename') else None)
        if not filename:
            return False, None, "No filename provided"
        
        # Check extension
        if not SecureFileUpload.is_allowed_extension(filename):
            allowed = ', '.join(SecureFileUpload.ALLOWED_EXTENSIONS)
            return False, None, f"File type not allowed. Allowed types: {allowed}"
        
        # Read file content
        try:
            # Save current position
            if hasattr(file, 'seek'):
                current_pos = file.tell()
                file.seek(0)
            
            file_content = file.read(SecureFileUpload.MAX_FILE_SIZE + 1)
            
            # Restore position
            if hasattr(file, 'seek'):
                file.seek(current_pos)
            
            # Check file size
            if len(file_content) > SecureFileUpload.MAX_FILE_SIZE:
                max_mb = SecureFileUpload.MAX_FILE_SIZE / (1024 * 1024)
                return False, None, f"File too large. Maximum size: {max_mb}MB"
            
            if len(file_content) == 0:
                return False, None, "File is empty"
            
            # Check MIME type
            mime_type = SecureFileUpload.get_file_mime_type(file_content, filename)
            
            # Allow application/octet-stream for Excel files (common false positive)
            if mime_type == 'application/octet-stream':
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in {'xlsx', 'xls'}:
                    mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if ext == 'xlsx' else 'application/vnd.ms-excel'
            
            # Validate MIME type (with some flexibility for Excel files)
            if mime_type not in SecureFileUpload.ALLOWED_MIME_TYPES:
                # Check if it's an Excel file by extension
                ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if ext in {'xlsx', 'xls'} and 'excel' in mime_type.lower():
                    # Allow Excel-related MIME types
                    pass
                else:
                    return False, mime_type, f"Invalid file type detected: {mime_type}"
            
            return True, mime_type, None
        
        except Exception as e:
            return False, None, f"File validation error: {str(e)}"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for secure storage.
        
        Args:
            filename: Original filename
        
        Returns:
            Sanitized filename
        """
        filename = Path(filename).name
        # Use Werkzeug's secure_filename
        sanitized = secure_filename(filename)
        
        # Additional security: remove any remaining dangerous characters
        sanitized = sanitized.replace('..', '').replace('/', '').replace('\\', '')
        
        return sanitized
    
    @staticmethod
    def calculate_file_hash(file_content: bytes) -> str:
        """
        Calculate SHA-256 hash of file content (for integrity checking).
        
        Args:
            file_content: File content bytes
        
        Returns:
            SHA-256 hash (hex string)
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def save_uploaded_file(file, upload_dir: str, custom_filename: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Save uploaded file securely.
        
        Args:
            file: File object from Flask request
            upload_dir: Directory to save file
            custom_filename: Optional custom filename (will be sanitized)
        
        Returns:
            Tuple of (success, file_path, error_message)
        """
        try:
            # Validate file first
            is_valid, mime_type, error = SecureFileUpload.validate_file(file)
            if not is_valid:
                return False, None, error
            
            # Read file content
            if hasattr(file, 'seek'):
                file.seek(0)
            file_content = file.read()
            
            # Create upload directory
            upload_path = Path(upload_dir)
            upload_path.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            if custom_filename:
                filename = SecureFileUpload.sanitize_filename(custom_filename)
            else:
                filename = SecureFileUpload.sanitize_filename(file.filename)
            
            # Ensure unique filename (prevent overwrites)
            file_path = upload_path / filename
            counter = 1
            while file_path.exists():
                name_part = file_path.stem
                ext_part = file_path.suffix
                file_path = upload_path / f"{name_part}_{counter}{ext_part}"
                counter += 1
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Set secure permissions (owner read/write only)
            os.chmod(file_path, 0o600)
            
            return True, str(file_path), None
        
        except Exception as e:
            return False, None, f"Failed to save file: {str(e)}"
