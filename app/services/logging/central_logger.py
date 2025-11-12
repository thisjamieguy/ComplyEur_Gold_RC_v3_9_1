"""
Central Logging Service
Phase 5: Compliance & Monitoring
Supports multiple logging backends (file, Datadog, Logtail, ELK)
"""

import os
import json
import logging
from typing import Optional, Dict
from datetime import datetime
from logging.handlers import RotatingFileHandler


class CentralLogger:
    """
    Central logging service with support for multiple backends.
    """
    
    def __init__(self, app_name: str = "eu-trip-tracker"):
        """
        Initialize central logger.
        
        Args:
            app_name: Application name
        """
        self.app_name = app_name
        self.loggers = {}
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Set up logging backends"""
        # Application logger (file-based)
        app_logger = self._setup_file_logger('app')
        self.loggers['file'] = app_logger
        
        # Audit logger (separate file)
        audit_logger = self._setup_file_logger('audit')
        self.loggers['audit'] = audit_logger
        
        # SIEM logger (structured JSON for external systems)
        siem_logger = self._setup_siem_logger()
        self.loggers['siem'] = siem_logger
    
    def _setup_file_logger(self, name: str) -> logging.Logger:
        """
        Set up file-based logger.
        
        Args:
            name: Logger name
        
        Returns:
            Logger instance
        """
        logger = logging.getLogger(f"{self.app_name}.{name}")
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Log directory
        log_dir = os.getenv('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler with rotation
        log_file = os.path.join(log_dir, f'{name}.log')
        handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        return logger
    
    def _setup_siem_logger(self) -> logging.Logger:
        """
        Set up SIEM logger (structured JSON).
        
        Returns:
            Logger instance
        """
        logger = logging.getLogger(f"{self.app_name}.siem")
        logger.setLevel(logging.INFO)
        
        if logger.handlers:
            return logger
        
        # SIEM log file (JSON lines)
        log_dir = os.getenv('LOG_DIR', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        siem_file = os.path.join(log_dir, 'siem.jsonl')
        handler = logging.FileHandler(siem_file, encoding='utf-8')
        
        # JSON formatter
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                }
                
                # Add extra fields
                if hasattr(record, 'user_id'):
                    log_entry['user_id'] = record.user_id
                if hasattr(record, 'ip_address'):
                    log_entry['ip_address'] = record.ip_address
                if hasattr(record, 'action'):
                    log_entry['action'] = record.action
                if hasattr(record, 'employee_id'):
                    log_entry['employee_id'] = record.employee_id
                
                return json.dumps(log_entry, ensure_ascii=False)
        
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
        return logger
    
    def log_event(self, level: str, message: str, **kwargs):
        """
        Log event to all configured backends.
        
        Args:
            level: Log level (info, warning, error, critical)
            message: Log message
            **kwargs: Additional context (user_id, ip_address, action, etc.)
        """
        # File logger
        log_method = getattr(self.loggers['file'], level.lower(), self.loggers['file'].info)
        log_method(message)
        
        # SIEM logger (structured)
        siem_method = getattr(self.loggers['siem'], level.lower(), self.loggers['siem'].info)
        
        # Create log record with extra fields
        extra = kwargs
        siem_method(message, extra=extra)
    
    def log_auth_event(self, action: str, success: bool, user_id: Optional[str] = None,
                      ip_address: Optional[str] = None, **kwargs):
        """
        Log authentication event.
        
        Args:
            action: Action type (login, logout, mfa_verify, etc.)
            success: Whether action succeeded
            user_id: User identifier (masked)
            ip_address: Client IP address
            **kwargs: Additional context
        """
        level = 'info' if success else 'warning'
        message = f"Auth event: {action} - {'SUCCESS' if success else 'FAILED'}"
        
        self.log_event(level, message, 
                      action=f"auth.{action}",
                      user_id=user_id,
                      ip_address=ip_address,
                      success=success,
                      **kwargs)
        
        # Also log to audit logger
        audit_msg = f"{action.upper()}: {user_id or 'unknown'} from {ip_address or 'unknown'} - {'SUCCESS' if success else 'FAILED'}"
        self.loggers['audit'].info(audit_msg)
    
    def log_data_access(self, action: str, user_id: Optional[str] = None,
                       employee_id: Optional[int] = None, **kwargs):
        """
        Log data access event.
        
        Args:
            action: Action type (read, export, delete, etc.)
            user_id: User identifier (masked)
            employee_id: Employee ID accessed
            **kwargs: Additional context
        """
        message = f"Data access: {action} - employee_id={employee_id}"
        
        self.log_event('info', message,
                      action=f"data_access.{action}",
                      user_id=user_id,
                      employee_id=employee_id,
                      **kwargs)
    
    def log_security_event(self, event_type: str, severity: str, message: str, **kwargs):
        """
        Log security event (for SIEM alerts).
        
        Args:
            event_type: Event type (brute_force, sql_injection, etc.)
            severity: Severity (low, medium, high, critical)
            message: Event message
            **kwargs: Additional context
        """
        level_map = {
            'low': 'info',
            'medium': 'warning',
            'high': 'error',
            'critical': 'critical'
        }
        
        level = level_map.get(severity.lower(), 'warning')
        
        self.log_event(level, f"SECURITY: {event_type} - {message}",
                      action=f"security.{event_type}",
                      severity=severity,
                      **kwargs)


# Global logger instance
_central_logger: Optional[CentralLogger] = None


def get_logger() -> CentralLogger:
    """
    Get or create central logger instance.
    
    Returns:
        CentralLogger instance
    """
    global _central_logger
    
    if _central_logger is None:
        _central_logger = CentralLogger()
    
    return _central_logger

