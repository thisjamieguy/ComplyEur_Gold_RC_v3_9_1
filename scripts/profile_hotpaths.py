#!/usr/bin/env python3
import os
import sys
import json
import csv
import time
import cProfile
import pstats
from datetime import date, timedelta
from io import StringIO

# Ensure project root on path
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, os.pardir))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from app import create_app
from app.services.rolling90 import presence_days, days_used_in_window


def ensure_reports_dir() -> str:
    project_root = _PROJECT_ROOT
    reports_dir = os.path.join(project_root, 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    return reports_dir


def profile_flask_endpoints(app, client, endpoints):
    results = []
    for name, method, path in endpoints:
        # Warm-up
        client.open(path, method=method)
        start = time.perf_counter()
        for _ in range(5):
            resp = client.open(path, method=method)
            _ = resp.status_code
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / 5.0) * 1000.0
        results.append({
            'endpoint': name,
            'method': method,
            'path': path,
            'avg_ms': round(avg_ms, 2)
        })
    return results


def synthetic_trips(num_trips: int, span_days: int = 365):
    trips = []
    start = date.today() - timedelta(days=span_days)
    step = max(3, span_days // max(1, num_trips))
    for i in range(num_trips):
        entry = start + timedelta(days=i * step)
        exit_ = entry + timedelta(days=min(10, max(1, step // 2)))
        trips.append({
            'country': 'FR',
            'entry_date': entry.isoformat(),
            'exit_date': exit_.isoformat(),
        })
    return trips


def profile_rolling90_kernels():
    kernels = []
    for trips_count in (50, 200, 1000):
        trips = synthetic_trips(trips_count, span_days=720)
        start = time.perf_counter()
        presence = presence_days(trips)
        t_presence = (time.perf_counter() - start) * 1000.0

        today = date.today()
        start = time.perf_counter()
        used = days_used_in_window(presence, today)
        t_window = (time.perf_counter() - start) * 1000.0

        kernels.append({
            'trips_count': trips_count,
            'presence_days_ms': round(t_presence, 2),
            'days_used_in_window_ms': round(t_window, 2),
            'presence_size': len(presence),
            'used_days_today': used,
        })
    return kernels


def run_cprofile_on_endpoint(app, client, path: str, method: str = 'GET'):
    pr = cProfile.Profile()
    pr.enable()
    resp = client.open(path, method=method)
    _ = resp.status_code
    pr.disable()
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumtime')
    ps.print_stats(30)
    return s.getvalue()


def main():
    reports_dir = ensure_reports_dir()

    app = create_app()
    app.testing = True

    with app.test_client() as client:
        endpoints = [
            ('employees', 'GET', '/api/employees'),
            ('trips_no_range', 'GET', '/api/trips'),
            ('health', 'GET', '/health')
        ]

        endpoint_timings = profile_flask_endpoints(app, client, endpoints)
        kernels = profile_rolling90_kernels()
        trips_profile = run_cprofile_on_endpoint(app, client, '/api/trips')

    summary = {
        'endpoint_timings': endpoint_timings,
        'rolling90_kernels': kernels,
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }
    json_path = os.path.join(reports_dir, 'profile_summary.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    csv_path = os.path.join(reports_dir, 'endpoint_timings.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['endpoint', 'method', 'path', 'avg_ms'])
        writer.writeheader()
        for row in endpoint_timings:
            writer.writerow(row)

    prof_txt_path = os.path.join(reports_dir, 'trips_cprofile.txt')
    with open(prof_txt_path, 'w', encoding='utf-8') as f:
        f.write(trips_profile)

    print(f"Wrote: {json_path}\nWrote: {csv_path}\nWrote: {prof_txt_path}")


if __name__ == '__main__':
    main()
