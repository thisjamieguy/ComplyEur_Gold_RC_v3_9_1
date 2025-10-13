import os
import hashlib
from datetime import datetime
from typing import Optional


def _ensure_parent(path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


def mask_identifier(identifier: str) -> str:
    if not identifier:
        return 'unknown'
    digest = hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:12]
    return f'user_{digest}'


def write_audit(log_path: str, action: str, admin_identifier: str, details: Optional[dict] = None) -> None:
    try:
        _ensure_parent(log_path)
        ts = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        masked = mask_identifier(admin_identifier)
        safe_details = {}
        if isinstance(details, dict):
            # copy without sensitive values
            for k, v in details.items():
                if v is None:
                    continue
                if any(x in k.lower() for x in ['password', 'secret', 'token']):
                    continue
                safe_details[k] = v
        line = {
            'ts': ts,
            'action': action,
            'admin': masked,
            'details': safe_details,
        }
        with open(log_path, 'a') as f:
            f.write(str(line) + '\n')
    except Exception:
        # Never break main flow due to logging errors
        pass




