import pytest
from datetime import date
from reference.oracle_calculator import calculate_days_used, rolling_window_violation


def test_basic_counts():
    trips = [{"entry":date(2025,1,1),"exit":date(2025,1,10)}]
    assert calculate_days_used(trips)==10


def test_rolling_violation():
    trips=[{"entry":date(2025,1,1),"exit":date(2025,3,31)}]
    res=rolling_window_violation(trips)
    assert res["total_used"]==90
    assert res["ok"]
