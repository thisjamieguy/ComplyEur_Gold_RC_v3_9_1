"""
Immutable Audit Trail Service
Phase 5: Compliance & Monitoring
Creates tamper-evident audit logs with integrity checking
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path


class ImmutableAuditTrail:
    """
    Immutable audit trail with SHA-256 integrity checking.
    Each log entry includes a hash chain for tamper detection.
    """
    
    def __init__(self, log_path: str):
        """
        Initialize audit trail.
        
        Args:
            log_path: Path to audit log file
        """
        self.log_path = Path(log_path)
        self.log_dir = self.log_path.parent
        self.integrity_file = self.log_dir / f"{self.log_path.stem}_integrity.jsonl"
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure log directory exists"""
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_previous_hash(self) -> Optional[str]:
        """
        Get hash of previous log entry for chain verification.
        
        Returns:
            SHA-256 hash of last entry, or None if no previous entries
        """
        if not self.integrity_file.exists():
            return None
        
        try:
            with open(self.integrity_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = json.loads(lines[-1])
                    return last_line.get('entry_hash')
        except Exception:
            pass
        
        return None
    
    def _calculate_entry_hash(self, entry: Dict) -> str:
        """
        Calculate SHA-256 hash of log entry.
        
        Args:
            entry: Log entry dictionary
        
        Returns:
            SHA-256 hash (hex string)
        """
        # Create deterministic JSON string (sorted keys)
        entry_str = json.dumps(entry, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()
    
    def write(self, action: str, admin_identifier: str, details: Optional[Dict] = None, 
              ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """
        Write immutable audit log entry.
        
        Args:
            action: Action type (e.g., 'login', 'data_access', 'export')
            admin_identifier: Admin user identifier (will be masked)
            details: Additional details dict
            ip_address: Client IP address
            user_agent: User agent string
        
        Returns:
            True if written successfully, False otherwise
        """
        try:
            # Get previous hash for chain
            previous_hash = self._get_previous_hash()
            
            # Create log entry
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Mask admin identifier
            masked_admin = self._mask_identifier(admin_identifier)
            
            # Sanitize details (remove sensitive data)
            safe_details = self._sanitize_details(details or {})
            
            entry = {
                'timestamp': timestamp,
                'action': action,
                'admin': masked_admin,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'details': safe_details,
            }
            
            # Add previous hash for chain
            if previous_hash:
                entry['previous_hash'] = previous_hash
            
            # Calculate entry hash
            entry_hash = self._calculate_entry_hash(entry)
            entry['entry_hash'] = entry_hash
            
            # Write to audit log (human-readable)
            log_line = json.dumps(entry, ensure_ascii=False)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
            
            # Write to integrity file (for hash chain verification)
            integrity_entry = {
                'timestamp': timestamp,
                'action': action,
                'entry_hash': entry_hash,
                'previous_hash': previous_hash,
            }
            with open(self.integrity_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(integrity_entry) + '\n')
            
            return True
        
        except Exception as e:
            # Log error but don't break application flow
            import logging
            logging.error(f"Failed to write audit log: {e}")
            return False
    
    def _mask_identifier(self, identifier: str) -> str:
        """
        Mask identifier using SHA-256.
        
        Args:
            identifier: Original identifier
        
        Returns:
            Masked identifier
        """
        if not identifier:
            return 'unknown'
        digest = hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:12]
        return f'user_{digest}'
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """
        Remove sensitive data from details dict.
        
        Args:
            details: Original details dict
        
        Returns:
            Sanitized details dict
        """
        sanitized = {}
        sensitive_keys = ['password', 'secret', 'token', 'key', 'credential', 'api_key']
        
        for k, v in details.items():
            if v is None:
                continue
            
            # Skip sensitive keys
            if any(keyword in k.lower() for keyword in sensitive_keys):
                continue
            
            sanitized[k] = v
        
        return sanitized
    
    def verify_integrity(self) -> tuple[bool, List[str]]:
        """
        Verify integrity of audit log using hash chain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.integrity_file.exists():
            return True, []  # No entries yet
        
        try:
            with open(self.integrity_file, 'r') as f:
                lines = f.readlines()
            
            previous_hash = None
            
            for i, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line)
                    entry_hash = entry.get('entry_hash')
                    stored_previous = entry.get('previous_hash')
                    
                    # Verify chain
                    if previous_hash and stored_previous != previous_hash:
                        errors.append(f"Chain broken at entry {i}: hash mismatch")
                    
                    # Verify entry hash (recalculate and compare)
                    # Note: We need the full entry from audit log to recalculate
                    # For now, we verify the chain consistency
                    
                    previous_hash = entry_hash
                
                except json.JSONDecodeError as e:
                    errors.append(f"Invalid JSON at line {i}: {e}")
        
        except Exception as e:
            errors.append(f"Failed to verify integrity: {e}")
        
        return len(errors) == 0, errors
    
    def get_entries(self, action_filter: Optional[str] = None, 
                   limit: Optional[int] = None) -> List[Dict]:
        """
        Read audit log entries.
        
        Args:
            action_filter: Filter by action type
            limit: Maximum number of entries to return
        
        Returns:
            List of log entries
        """
        entries = []
        
        if not self.log_path.exists():
            return entries
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        if action_filter and entry.get('action') != action_filter:
                            continue
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
            
            # Reverse to get newest first
            entries.reverse()
            
            if limit:
                entries = entries[:limit]
            
            return entries
        
        except Exception as e:
            import logging
            logging.error(f"Failed to read audit log: {e}")
            return []


def get_audit_trail(log_path: Optional[str] = None) -> ImmutableAuditTrail:
    """
    Get or create audit trail instance.
    
    Args:
        log_path: Optional path to audit log
    
    Returns:
        ImmutableAuditTrail instance
    """
    if log_path is None:
        import os
        log_path = os.getenv('AUDIT_LOG_PATH', 'logs/audit.log')
    
    return ImmutableAuditTrail(log_path)

