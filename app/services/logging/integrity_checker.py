"""
Log Integrity Checker
Phase 5: Compliance & Monitoring
Daily SHA-256 hash verification for audit logs
"""

import os
import json
import hashlib
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class LogIntegrityChecker:
    """
    Daily log integrity checker using SHA-256.
    Creates integrity hashes and verifies log tampering.
    """
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize integrity checker.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
        self.integrity_dir = self.log_dir / "integrity"
        self.integrity_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
        
        Returns:
            SHA-256 hash (hex string)
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def check_log_integrity(self, log_file: str, date_check: Optional[date] = None) -> Tuple[bool, Dict]:
        """
        Check integrity of log file.
        
        Args:
            log_file: Name of log file (e.g., 'audit.log')
            date_check: Optional date to check (defaults to today)
        
        Returns:
            Tuple of (is_valid, result_dict)
        """
        if date_check is None:
            date_check = date.today()
        
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            return False, {
                'error': f'Log file not found: {log_file}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
        
        # Calculate current hash
        current_hash = self.calculate_file_hash(log_path)
        
        # Check against stored hash
        integrity_file = self.integrity_dir / f"{log_file}.{date_check.isoformat()}.hash"
        
        result = {
            'log_file': log_file,
            'date': date_check.isoformat(),
            'current_hash': current_hash,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'file_size': log_path.stat().st_size,
        }
        
        if integrity_file.exists():
            try:
                with open(integrity_file, 'r') as f:
                    stored_data = json.load(f)
                    stored_hash = stored_data.get('hash')
                    stored_date = stored_data.get('date')
                
                if stored_hash == current_hash:
                    result['status'] = 'valid'
                    result['stored_hash'] = stored_hash
                    result['previous_check'] = stored_date
                    return True, result
                else:
                    result['status'] = 'tampered'
                    result['stored_hash'] = stored_hash
                    result['previous_check'] = stored_date
                    result['warning'] = 'Hash mismatch detected - possible tampering!'
                    return False, result
            
            except Exception as e:
                result['status'] = 'error'
                result['error'] = f'Failed to read stored hash: {e}'
                return False, result
        else:
            # First check for this file/date
            result['status'] = 'new'
            result['note'] = 'First integrity check for this file/date'
            return True, result
    
    def store_integrity_hash(self, log_file: str, date_check: Optional[date] = None) -> bool:
        """
        Store integrity hash for log file.
        
        Args:
            log_file: Name of log file
            date_check: Optional date (defaults to today)
        
        Returns:
            True if stored successfully
        """
        if date_check is None:
            date_check = date.today()
        
        log_path = self.log_dir / log_file
        
        if not log_path.exists():
            return False
        
        # Calculate hash
        file_hash = self.calculate_file_hash(log_path)
        
        # Store hash
        integrity_file = self.integrity_dir / f"{log_file}.{date_check.isoformat()}.hash"
        
        try:
            data = {
                'log_file': log_file,
                'date': date_check.isoformat(),
                'hash': file_hash,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'file_size': log_path.stat().st_size,
            }
            
            with open(integrity_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        
        except Exception as e:
            import logging
            logging.error(f"Failed to store integrity hash: {e}")
            return False
    
    def check_all_logs(self) -> Dict[str, Tuple[bool, Dict]]:
        """
        Check integrity of all log files.
        
        Returns:
            Dict mapping log file names to (is_valid, result_dict)
        """
        results = {}
        
        # List of log files to check
        log_files = [
            'audit.log',
            'app.log',
            'auth.log',
            'siem.jsonl',
        ]
        
        for log_file in log_files:
            log_path = self.log_dir / log_file
            if log_path.exists():
                is_valid, result = self.check_log_integrity(log_file)
                results[log_file] = (is_valid, result)
        
        return results
    
    def daily_integrity_check(self) -> Dict:
        """
        Perform daily integrity check for all logs.
        
        Returns:
            Summary dictionary
        """
        today = date.today()
        
        # Check all logs
        checks = self.check_all_logs()
        
        # Store hashes for today
        for log_file in checks.keys():
            self.store_integrity_hash(log_file, today)
        
        # Summary
        valid_count = sum(1 for is_valid, _ in checks.values() if is_valid)
        total_count = len(checks)
        
        summary = {
            'date': today.isoformat(),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_files': total_count,
            'valid_files': valid_count,
            'invalid_files': total_count - valid_count,
            'checks': {log_file: result for log_file, (is_valid, result) in checks.items()},
        }
        
        # Store summary
        summary_file = self.integrity_dir / f"daily_check.{today.isoformat()}.json"
        try:
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
        except Exception as e:
            import logging
            logging.error(f"Failed to store daily check summary: {e}")
        
        return summary


def get_integrity_checker(log_dir: Optional[str] = None) -> LogIntegrityChecker:
    """
    Get or create integrity checker instance.
    
    Args:
        log_dir: Optional log directory path
    
    Returns:
        LogIntegrityChecker instance
    """
    if log_dir is None:
        log_dir = os.getenv('LOG_DIR', 'logs')
    
    return LogIntegrityChecker(log_dir)

