"""
Data Masking Utilities
Mask sensitive data for display (passport/ID numbers, etc.)
"""

import re
from typing import Optional


class DataMasking:
    """
    Utility class for masking sensitive personal data.
    Implements partial masking (last N digits visible) for audit trails.
    """
    
    @staticmethod
    def mask_passport_number(passport_number: str, visible_digits: int = 3) -> str:
        """
        Mask passport number, showing only last N digits.
        
        Example: "AB12345678" -> "********78" (last 2 digits visible)
        
        Args:
            passport_number: Full passport number
            visible_digits: Number of trailing digits to show (default: 3)
        
        Returns:
            Masked passport number
        """
        if not passport_number or len(passport_number) <= visible_digits:
            return "*" * len(passport_number) if passport_number else ""
        
        mask_length = len(passport_number) - visible_digits
        return "*" * mask_length + passport_number[-visible_digits:]
    
    @staticmethod
    def mask_id_number(id_number: str, visible_digits: int = 3) -> str:
        """
        Mask ID number, showing only last N digits.
        
        Args:
            id_number: Full ID number
            visible_digits: Number of trailing digits to show (default: 3)
        
        Returns:
            Masked ID number
        """
        return DataMasking.mask_passport_number(id_number, visible_digits)
    
    @staticmethod
    def mask_email(email: str) -> str:
        """
        Mask email address, showing only first letter and domain.
        
        Example: "john.doe@example.com" -> "j***@example.com"
        
        Args:
            email: Email address
        
        Returns:
            Masked email address
        """
        if not email or '@' not in email:
            return email
        
        local, domain = email.split('@', 1)
        if len(local) <= 1:
            masked_local = local
        else:
            masked_local = f"{local[0]}***"
        
        return f"{masked_local}@{domain}"
    
    @staticmethod
    def mask_name(name: str) -> str:
        """
        Mask full name, showing only first letter of first name and last name.
        
        Example: "John Doe" -> "J*** D***"
        
        Args:
            name: Full name
        
        Returns:
            Masked name
        """
        if not name:
            return ""
        
        parts = name.split()
        masked_parts = []
        
        for part in parts:
            if len(part) <= 1:
                masked_parts.append(part)
            else:
                masked_parts.append(f"{part[0]}***")
        
        return " ".join(masked_parts)
    
    @staticmethod
    def mask_phone_number(phone_number: str, visible_digits: int = 4) -> str:
        """
        Mask phone number, showing only last N digits.
        
        Example: "+1-555-123-4567" -> "***-***-4567"
        
        Args:
            phone_number: Phone number
            visible_digits: Number of trailing digits to show (default: 4)
        
        Returns:
            Masked phone number
        """
        if not phone_number or len(phone_number) <= visible_digits:
            return "*" * len(phone_number) if phone_number else ""
        
        # Extract digits
        digits = re.sub(r'\D', '', phone_number)
        if len(digits) <= visible_digits:
            return "*" * len(phone_number)
        
        # Mask all but last N digits
        masked_digits = "*" * (len(digits) - visible_digits) + digits[-visible_digits:]
        
        # Try to preserve format
        if re.match(r'^\+?\d+[-.\s]?\d+[-.\s]?\d+', phone_number):
            # Format: preserve structure if possible
            return "*" * (len(phone_number) - visible_digits) + phone_number[-visible_digits:]
        
        return masked_digits
