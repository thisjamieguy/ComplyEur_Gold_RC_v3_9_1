"""
Independent reference calculator for ComplyEur 90/180 rule.

Implements a clean, standalone algorithm to compare against production logic.
"""
from datetime import date, timedelta
from typing import List, Dict


def calculate_days_used(trips: List[Dict]) -> int:
    days = set()
    for t in trips:
        entry = t["entry"]
        exit_ = t["exit"]
        d = entry
        while d <= exit_:
            days.add(d)
            d += timedelta(days=1)
    return len(days)


def rolling_window_violation(trips: List[Dict], window_days:int=180, limit:int=90) -> Dict:
    trips = sorted(trips, key=lambda x: x["entry"])
    all_days = []
    for t in trips:
        d = t["entry"]
        while d <= t["exit"]:
            all_days.append(d)
            d += timedelta(days=1)
    all_days = sorted(set(all_days))
    violations = []
    for d in all_days:
        window = [x for x in all_days if (d - timedelta(days=window_days)) <= x <= d]
        if len(window) > limit:
            violations.append(d)
    return {
        "total_used": len(all_days),
        "violations": violations,
        "ok": len(violations) == 0,
        "next_legal_entry": (max(all_days)+timedelta(days=1)) if not violations else None
    }
