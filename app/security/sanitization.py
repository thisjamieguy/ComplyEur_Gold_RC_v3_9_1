"""
Input Sanitization Module
Whitelisting and regex-based sanitization for all user inputs
"""

import re
import html
from typing import Optional, Callable
from markupsafe import Markup, escape

try:
    from bleach import clean
    _bleach_available = True
except ImportError:
    _bleach_available = False


class InputSanitizer:
    """
    Enterprise input sanitization with whitelisting approach.
    Escapes all potentially dangerous characters and patterns.
    """
    
    # Whitelist patterns for common input types
    PATTERNS = {
        'name': re.compile(r'^[a-zA-Z\s\-\'\.]{1,100}$'),
        'country_code': re.compile(r'^[A-Z]{2}$'),
        'date': re.compile(r'^\d{4}-\d{2}-\d{2}$'),
        'integer': re.compile(r'^-?\d+$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9\s\-_]{1,200}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'url': re.compile(r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'),
    }
    
    # Allowed HTML tags for rich text (if needed in future)
    ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000, strip: bool = True) -> str:
        """
        Sanitize a string input.
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            strip: Whether to strip whitespace
        
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        if strip:
            value = value.strip()
        
        # HTML escape to prevent XSS
        value = html.escape(value)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def sanitize_name(name: str) -> str:
        """
        Sanitize employee name (whitelist: letters, spaces, hyphens, apostrophes, dots).
        
        Args:
            name: Employee name
        
        Returns:
            Sanitized name
        
        Raises:
            ValueError: If name doesn't match pattern
        """
        if not name:
            return ""
        
        name = name.strip()
        
        # Whitelist: only letters, spaces, hyphens, apostrophes, dots
        # Remove any characters not in whitelist
        sanitized = re.sub(r'[^a-zA-Z\s\-\'\.]', '', name)
        
        # Validate length
        if len(sanitized) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(sanitized) > 100:
            raise ValueError("Name must be no more than 100 characters")
        
        # Validate pattern
        if not InputSanitizer.PATTERNS['name'].match(sanitized):
            raise ValueError("Name contains invalid characters")
        
        return sanitized
    
    @staticmethod
    def sanitize_country_code(country_code: str) -> str:
        """
        Sanitize country code (2-letter ISO code).
        
        Args:
            country_code: Country code
        
        Returns:
            Uppercase 2-letter code
        
        Raises:
            ValueError: If invalid format
        """
        if not country_code:
            return ""
        
        country_code = country_code.strip().upper()
        
        if not InputSanitizer.PATTERNS['country_code'].match(country_code):
            raise ValueError(f"Invalid country code format: {country_code}")
        
        return country_code
    
    @staticmethod
    def sanitize_date(date_str: str) -> str:
        """
        Sanitize date string (YYYY-MM-DD format).
        
        Args:
            date_str: Date string
        
        Returns:
            Validated date string
        
        Raises:
            ValueError: If invalid format
        """
        if not date_str:
            return ""
        
        date_str = date_str.strip()
        
        if not InputSanitizer.PATTERNS['date'].match(date_str):
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got: {date_str}")
        
        # Additional validation: try to parse
        from datetime import datetime
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date: {date_str}")
        
        return date_str
    
    @staticmethod
    def sanitize_integer(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """
        Sanitize integer input.
        
        Args:
            value: String representation of integer
            min_val: Minimum allowed value
            max_val: Maximum allowed value
        
        Returns:
            Integer value
        
        Raises:
            ValueError: If invalid format or out of range
        """
        if not value:
            raise ValueError("Value is required")
        
        value = value.strip()
        
        if not InputSanitizer.PATTERNS['integer'].match(value):
            raise ValueError(f"Invalid integer format: {value}")
        
        int_value = int(value)
        
        if min_val is not None and int_value < min_val:
            raise ValueError(f"Value must be at least {min_val}")
        if max_val is not None and int_value > max_val:
            raise ValueError(f"Value must be at most {max_val}")
        
        return int_value
    
    @staticmethod
    def sanitize_html(html_content: str, allowed_tags: Optional[list] = None) -> str:
        """
        Sanitize HTML content using bleach.
        
        Args:
            html_content: HTML string
            allowed_tags: List of allowed HTML tags (default: minimal set)
        
        Returns:
            Sanitized HTML
        """
        if not html_content:
            return ""
        
        if not _bleach_available:
            # Fallback: basic HTML escaping
            return html.escape(html_content)
        
        if allowed_tags is None:
            allowed_tags = InputSanitizer.ALLOWED_TAGS
        
        # Use bleach to clean HTML
        cleaned = clean(
            html_content,
            tags=allowed_tags,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    @staticmethod
    def escape_for_template(value: str) -> Markup:
        """
        Escape value for safe use in templates.
        
        Args:
            value: String to escape
        
        Returns:
            Markup object (Flask/Jinja2 safe)
        """
        return escape(value)

