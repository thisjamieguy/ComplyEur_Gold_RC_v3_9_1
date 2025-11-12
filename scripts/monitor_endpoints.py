#!/usr/bin/env python3
import os
import sys
import csv
import time
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app import create_app


def ensure_reports_dir() -> str:
    reports_dir = os.path.join(_PROJECT_ROOT, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def main():
    reports_dir = ensure_reports_dir()
    csv_path = os.path.join(reports_dir, 'endpoint_monitor.csv')

    app = create_app()
    app.testing = True

    endpoints = [
        ('employees', 'GET', '/api/employees'),
        ('trips', 'GET', '/api/trips'),
        ('health', 'GET', '/health'),
    ]

    with app.test_client() as client:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        rows = []
        for name, method, path in endpoints:
            # One warmup
            client.open(path, method=method)
            start = time.perf_counter()
            resp = client.open(path, method=method)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            rows.append({
                'timestamp': timestamp,
                'endpoint': name,
                'method': method,
                'path': path,
                'status': resp.status_code,
                'latency_ms': round(elapsed_ms, 2),
            })

    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp','endpoint','method','path','status','latency_ms'])
        if write_header:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Appended {len(rows)} rows to {csv_path}")


if __name__ == '__main__':
    main()

