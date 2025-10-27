"""
Date utilities for consistent date formatting and parsing across the application.
Standardizes on DD-MM-YYYY format for user-facing dates.
"""

from datetime import datetime, date
from typing import Optional


FORMAT_DDMMYYYY = "%d-%m-%Y"
FORMAT_YYYYMMDD = "%Y-%m-%d"


def parse_ddmmyyyy(date_str: str) -> datetime:
    """
    Parse a date string in DD-MM-YYYY format to datetime object.
    
    Args:
        date_str: Date string in DD-MM-YYYY format
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date string is invalid
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string is required")
    
    return datetime.strptime(date_str.strip(), FORMAT_DDMMYYYY)


def format_ddmmyyyy(dt: datetime) -> str:
    """
    Format a datetime object to DD-MM-YYYY string.
    
    Args:
        dt: datetime object
        
    Returns:
        Date string in DD-MM-YYYY format
    """
    return dt.strftime(FORMAT_DDMMYYYY)


def parse_yyyymmdd(date_str: str) -> datetime:
    """
    Parse a date string in YYYY-MM-DD format to datetime object.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date string is invalid
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string is required")
    
    return datetime.strptime(date_str.strip(), FORMAT_YYYYMMDD)


def format_yyyymmdd(dt: datetime) -> str:
    """
    Format a datetime object to YYYY-MM-DD string.
    
    Args:
        dt: datetime object
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    return dt.strftime(FORMAT_YYYYMMDD)


def safe_parse_date(date_str: str, expected_format: str = FORMAT_YYYYMMDD) -> Optional[datetime]:
    """
    Safely parse a date string, returning None if parsing fails.
    
    Args:
        date_str: Date string to parse
        expected_format: Expected format (default: YYYY-MM-DD)
        
    Returns:
        datetime object or None if parsing fails
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    try:
        return datetime.strptime(date_str.strip(), expected_format)
    except (ValueError, TypeError):
        return None


def convert_ddmmyyyy_to_yyyymmdd(date_str: str) -> str:
    """
    Convert date from DD-MM-YYYY to YYYY-MM-DD format.
    
    Args:
        date_str: Date string in DD-MM-YYYY format
        
    Returns:
        Date string in YYYY-MM-DD format
        
    Raises:
        ValueError: If date string is invalid
    """
    dt = parse_ddmmyyyy(date_str)
    return format_yyyymmdd(dt)


def convert_yyyymmdd_to_ddmmyyyy(date_str: str) -> str:
    """
    Convert date from YYYY-MM-DD to DD-MM-YYYY format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Date string in DD-MM-YYYY format
        
    Raises:
        ValueError: If date string is invalid
    """
    dt = parse_yyyymmdd(date_str)
    return format_ddmmyyyy(dt)
