"""
Input Validation Module
Comprehensive validation with whitelisting and regex patterns
"""

import re
from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List, Dict
from .sanitization import InputSanitizer


class InputValidator:
    """
    Enterprise input validation with whitelisting approach.
    Validates all inputs before processing.
    """
    
    # Country code whitelist (Schengen + EU)
    VALID_COUNTRY_CODES = {
        'AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
        'DE', 'GR', 'HU', 'IS', 'IE', 'IT', 'LV', 'LI', 'LT', 'LU',
        'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE',
        'CH', 'XX'  # XX for private trips
    }
    
    @staticmethod
    def validate_employee_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate employee name.
        
        Args:
            name: Employee name
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Employee name is required"
        
        if len(name.strip()) < 2:
            return False, "Employee name must be at least 2 characters"
        
        if len(name.strip()) > 100:
            return False, "Employee name must be no more than 100 characters"
        
        # Whitelist: letters, spaces, hyphens, apostrophes, dots
        if not re.match(r'^[a-zA-Z\s\-\'\.]+$', name.strip()):
            return False, "Employee name contains invalid characters. Only letters, spaces, hyphens, apostrophes, and dots are allowed"
        
        return True, None
    
    @staticmethod
    def validate_country_code(country_code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate country code against whitelist.
        
        Args:
            country_code: 2-letter country code
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not country_code:
            return False, "Country code is required"
        
        country_code = country_code.strip().upper()
        
        if country_code not in InputValidator.VALID_COUNTRY_CODES:
            return False, f"Invalid country code: {country_code}. Must be a valid EU/Schengen country code."
        
        return True, None
    
    @staticmethod
    def validate_date(date_str: str, allow_future: bool = True, allow_past: bool = True,
                     max_years_past: int = 10, max_years_future: int = 2) -> Tuple[bool, Optional[str]]:
        """
        Validate date string.
        
        Args:
            date_str: Date string (YYYY-MM-DD)
            allow_future: Allow future dates
            allow_past: Allow past dates
            max_years_past: Maximum years in past
            max_years_future: Maximum years in future
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is required"
        
        # Format validation
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str.strip()):
            return False, "Invalid date format. Expected YYYY-MM-DD"
        
        try:
            parsed_date = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
        except ValueError:
            return False, f"Invalid date: {date_str}"
        
        today = date.today()
        
        # Check future/past constraints
        if not allow_future and parsed_date > today:
            return False, "Future dates are not allowed"
        
        if not allow_past and parsed_date < today:
            return False, "Past dates are not allowed"
        
        # Check range constraints
        max_past = today - timedelta(days=max_years_past * 365)
        if parsed_date < max_past:
            return False, f"Date is more than {max_years_past} years in the past"
        
        max_future = today + timedelta(days=max_years_future * 365)
        if parsed_date > max_future:
            return False, f"Date is more than {max_years_future} years in the future"
        
        return True, None
    
    @staticmethod
    def validate_date_range(entry_date: str, exit_date: str) -> Tuple[bool, Optional[str]]:
        """
        Validate date range (exit must be after entry).
        
        Args:
            entry_date: Entry date string
            exit_date: Exit date string
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate individual dates
        entry_valid, entry_error = InputValidator.validate_date(entry_date)
        if not entry_valid:
            return False, f"Entry date: {entry_error}"
        
        exit_valid, exit_error = InputValidator.validate_date(exit_date)
        if not exit_valid:
            return False, f"Exit date: {exit_error}"
        
        # Parse dates
        entry_dt = datetime.strptime(entry_date.strip(), '%Y-%m-%d').date()
        exit_dt = datetime.strptime(exit_date.strip(), '%Y-%m-%d').date()
        
        # Check exit > entry
        if exit_dt <= entry_dt:
            return False, "Exit date must be after entry date"
        
        # Check maximum duration (2 years)
        duration_days = (exit_dt - entry_dt).days
        if duration_days > 730:  # 2 years
            return False, "Trip duration cannot exceed 2 years"
        
        return True, None
    
    @staticmethod
    def validate_integer(value: str, min_val: Optional[int] = None, max_val: Optional[int] = None,
                        field_name: str = "Value") -> Tuple[bool, Optional[str]]:
        """
        Validate integer input.
        
        Args:
            value: String representation of integer
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Field name for error messages
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            return False, f"{field_name} is required"
        
        try:
            int_value = int(value.strip())
        except ValueError:
            return False, f"{field_name} must be a valid number"
        
        if min_val is not None and int_value < min_val:
            return False, f"{field_name} must be at least {min_val}"
        
        if max_val is not None and int_value > max_val:
            return False, f"{field_name} must be at most {max_val}"
        
        return True, None
    
    @staticmethod
    def validate_all_trip_fields(data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate all trip fields at once.
        
        Args:
            data: Dictionary with trip fields
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Employee ID
        if 'employee_id' in data:
            valid, error = InputValidator.validate_integer(
                str(data['employee_id']), min_val=1, field_name="Employee ID"
            )
            if not valid:
                errors.append(error)
        
        # Country code
        if 'country_code' in data or 'country' in data:
            country = data.get('country_code') or data.get('country', '')
            valid, error = InputValidator.validate_country_code(country)
            if not valid:
                errors.append(error)
        
        # Entry date
        if 'entry_date' in data:
            valid, error = InputValidator.validate_date(data['entry_date'])
            if not valid:
                errors.append(error)
        
        # Exit date
        if 'exit_date' in data and data['exit_date']:
            valid, error = InputValidator.validate_date(data['exit_date'])
            if not valid:
                errors.append(error)
        
        # Date range
        if 'entry_date' in data and 'exit_date' in data and data.get('exit_date'):
            valid, error = InputValidator.validate_date_range(data['entry_date'], data['exit_date'])
            if not valid:
                errors.append(error)
        
        return len(errors) == 0, errors

