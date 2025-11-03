"""
SIEM Alert Configuration
Phase 5: Compliance & Monitoring
Defines security alerts for SIEM integration
"""

from typing import Dict, List
from app.services.logging.central_logger import get_logger


class SIEMAlerts:
    """
    SIEM alert definitions and triggering logic.
    """
    
    # Alert thresholds
    FAILED_LOGIN_THRESHOLD = 10  # Failed logins per minute
    BULK_EXPORT_THRESHOLD = 5  # Exports per hour
    UNUSUAL_ACCESS_THRESHOLD = 20  # Unusual access patterns
    
    @staticmethod
    def alert_failed_logins(count: int, ip_address: str, time_window: str = "1 minute"):
        """
        Alert on excessive failed login attempts.
        
        Args:
            count: Number of failed attempts
            ip_address: Source IP address
            time_window: Time window for threshold
        """
        if count >= SIEMAlerts.FAILED_LOGIN_THRESHOLD:
            logger = get_logger()
            logger.log_security_event(
                event_type='brute_force',
                severity='high',
                message=f'Excessive failed login attempts: {count} attempts from {ip_address} in {time_window}',
                ip_address=ip_address,
                count=count,
                threshold=SIEMAlerts.FAILED_LOGIN_THRESHOLD
            )
    
    @staticmethod
    def alert_bulk_export(count: int, user_id: str, employee_ids: List[int]):
        """
        Alert on bulk export operations.
        
        Args:
            count: Number of exports
            user_id: User identifier (masked)
            employee_ids: List of employee IDs exported
        """
        if count >= SIEMAlerts.BULK_EXPORT_THRESHOLD:
            logger = get_logger()
            logger.log_security_event(
                event_type='bulk_export',
                severity='medium',
                message=f'Bulk export detected: {count} exports by {user_id}',
                user_id=user_id,
                export_count=count,
                employee_ids=employee_ids[:10],  # Limit to first 10
                threshold=SIEMAlerts.BULK_EXPORT_THRESHOLD
            )
    
    @staticmethod
    def alert_unusual_access(user_id: str, action: str, count: int):
        """
        Alert on unusual access patterns.
        
        Args:
            user_id: User identifier (masked)
            action: Action type
            count: Number of actions
        """
        if count >= SIEMAlerts.UNUSUAL_ACCESS_THRESHOLD:
            logger = get_logger()
            logger.log_security_event(
                event_type='unusual_access',
                severity='medium',
                message=f'Unusual access pattern: {count} {action} actions by {user_id}',
                user_id=user_id,
                action=action,
                count=count,
                threshold=SIEMAlerts.UNUSUAL_ACCESS_THRESHOLD
            )
    
    @staticmethod
    def alert_data_breach_attempt(action: str, ip_address: str, details: Dict):
        """
        Alert on potential data breach attempt.
        
        Args:
            action: Action type
            ip_address: Source IP address
            details: Additional details
        """
        logger = get_logger()
        logger.log_security_event(
            event_type='data_breach_attempt',
            severity='critical',
            message=f'Potential data breach attempt: {action} from {ip_address}',
            ip_address=ip_address,
            action=action,
            **details
        )
    
    @staticmethod
    def alert_integrity_violation(log_file: str, error: str):
        """
        Alert on log integrity violation.
        
        Args:
            log_file: Name of log file
            error: Integrity error description
        """
        logger = get_logger()
        logger.log_security_event(
            event_type='log_integrity_violation',
            severity='high',
            message=f'Log integrity violation detected: {log_file} - {error}',
            log_file=log_file,
            error=error
        )

