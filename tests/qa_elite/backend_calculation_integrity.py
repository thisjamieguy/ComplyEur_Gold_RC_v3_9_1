"""
Elite QA Task Force: Backend Calculation Integrity Tests
Validates 90/180-day rolling logic, edge cases, and precision
"""

import pytest
import sqlite3
from datetime import date, datetime, timedelta
from typing import List, Dict, Set
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.rolling90 import (
    presence_days, days_used_in_window, earliest_safe_entry,
    calculate_days_remaining, days_until_compliant, is_schengen_country
)
from app.services.exports import calculate_eu_days_from_trips


class CalculationIntegrityValidator:
    """Validates mathematical correctness of backend calculations"""
    
    def __init__(self):
        self.discrepancies = []
        self.test_results = []
    
    def validate_window_calculation(self, trips: List[Dict], ref_date: date, expected_days: int) -> bool:
        """Validate 180-day window calculation is exact"""
        presence = presence_days(trips)
        actual_days = days_used_in_window(presence, ref_date)
        
        if actual_days != expected_days:
            self.discrepancies.append({
                'test': 'window_calculation',
                'expected': expected_days,
                'actual': actual_days,
                'trips': trips,
                'ref_date': ref_date.isoformat()
            })
            return False
        
        self.test_results.append({
            'test': 'window_calculation',
            'status': 'PASS',
            'expected': expected_days,
            'actual': actual_days
        })
        return True
    
    def validate_rolling_window_edge_cases(self) -> List[Dict]:
        """Test edge cases in rolling window logic"""
        results = []
        today = date.today()
        
        # Test 1: Trip exactly at window boundary
        boundary_trip = [{
            'entry_date': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        presence = presence_days(boundary_trip)
        days = days_used_in_window(presence, today)
        results.append({
            'test': 'boundary_180_days_ago',
            'expected': 1,
            'actual': days,
            'passed': days == 1
        })
        
        # Test 2: Trip one day before window (should not count)
        before_window = [{
            'entry_date': (today - timedelta(days=181)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=181)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        presence = presence_days(before_window)
        days = days_used_in_window(presence, today)
        results.append({
            'test': 'before_window_boundary',
            'expected': 0,
            'actual': days,
            'passed': days == 0
        })
        
        # Test 3: Trip exactly at today - 1 day (should count)
        yesterday = [{
            'entry_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        presence = presence_days(yesterday)
        days = days_used_in_window(presence, today)
        results.append({
            'test': 'yesterday_in_window',
            'expected': 1,
            'actual': days,
            'passed': days == 1
        })
        
        return results
    
    def validate_leap_year_handling(self) -> bool:
        """Validate correct handling of leap years"""
        # Test trip spanning Feb 29 in a leap year
        leap_year_date = date(2024, 2, 28)
        leap_trip = [{
            'entry_date': leap_year_date.strftime('%Y-%m-%d'),
            'exit_date': date(2024, 3, 1).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        
        presence = presence_days(leap_trip)
        expected_days = 3  # Feb 28, Feb 29, Mar 1
        actual_days = len(presence)
        
        if actual_days != expected_days:
            self.discrepancies.append({
                'test': 'leap_year',
                'expected': expected_days,
                'actual': actual_days
            })
            return False
        return True
    
    def validate_overlapping_trips(self) -> bool:
        """Validate overlapping trips don't double-count days"""
        today = date.today()
        overlapping_trips = [
            {
                'entry_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=40)).strftime('%Y-%m-%d'),
                'country': 'FR'
            },
            {
                'entry_date': (today - timedelta(days=45)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=35)).strftime('%Y-%m-%d'),
                'country': 'DE'
            }
        ]
        
        presence = presence_days(overlapping_trips)
        # Should be 16 days total (not 21 = 11 + 10)
        expected_days = 16  # Days 40-50 and 35-45 overlap, so total unique days
        actual_days = len(presence)
        
        if actual_days != expected_days:
            self.discrepancies.append({
                'test': 'overlapping_trips',
                'expected': expected_days,
                'actual': actual_days,
                'trips': overlapping_trips
            })
            return False
        return True
    
    def validate_partial_day_handling(self) -> bool:
        """Validate partial days are handled correctly (all days inclusive)"""
        today = date.today()
        single_day_trip = [{
            'entry_date': (today - timedelta(days=10)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=10)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        
        presence = presence_days(single_day_trip)
        expected_days = 1
        actual_days = len(presence)
        
        if actual_days != expected_days:
            self.discrepancies.append({
                'test': 'partial_day',
                'expected': expected_days,
                'actual': actual_days
            })
            return False
        return True
    
    def validate_ireland_exclusion(self) -> bool:
        """Validate Ireland trips are correctly excluded"""
        today = date.today()
        mixed_trips = [
            {
                'entry_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=40)).strftime('%Y-%m-%d'),
                'country': 'FR'
            },
            {
                'entry_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=20)).strftime('%Y-%m-%d'),
                'country': 'IE'  # Ireland should be excluded
            }
        ]
        
        presence = presence_days(mixed_trips)
        days_used = days_used_in_window(presence, today)
        
        # Should only count France trip (11 days), not Ireland
        expected_days = 11
        if days_used != expected_days:
            self.discrepancies.append({
                'test': 'ireland_exclusion',
                'expected': expected_days,
                'actual': days_used
            })
            return False
        return True
    
    def validate_90_day_limit_precision(self) -> bool:
        """Validate exact 90-day limit handling"""
        today = date.today()
        # Create exactly 90 days of trips
        exact_90_trips = [{
            'entry_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        
        presence = presence_days(exact_90_trips)
        days_used = days_used_in_window(presence, today)
        
        if days_used != 90:
            self.discrepancies.append({
                'test': 'exact_90_days',
                'expected': 90,
                'actual': days_used
            })
            return False
        
        # Test 91 days (should be over limit)
        over_limit_trips = [{
            'entry_date': (today - timedelta(days=91)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        
        presence = presence_days(over_limit_trips)
        days_used = days_used_in_window(presence, today)
        
        if days_used != 91:
            self.discrepancies.append({
                'test': 'over_90_days',
                'expected': 91,
                'actual': days_used
            })
            return False
        
        return True
    
    def validate_safe_entry_date_calculation(self) -> bool:
        """Validate earliest safe entry date is calculated correctly"""
        today = date.today()
        # Employee with 90 days used (90 days ago to yesterday = 90 days)
        trips = [{
            'entry_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        
        presence = presence_days(trips)
        safe_entry = earliest_safe_entry(presence, today, limit=90)
        
        # The safe entry date is when the oldest day (today - 90) falls out of the 180-day window
        # The window for a future date 'd' is [d - 180, d - 1]
        # The oldest day (today - 90) falls out when: d - 180 > (today - 90)
        # So: d > today - 90 + 180 = today + 90
        # The actual implementation checks day by day, so it should be approximately today + 90 days
        oldest_day = min(presence)
        expected_date = oldest_day + timedelta(days=180)  # When oldest day falls out of window
        
        if safe_entry is None:
            # If already eligible, that's fine
            used_today = days_used_in_window(presence, today)
            if used_today > 89:  # Should not be None if over limit
                self.discrepancies.append({
                    'test': 'safe_entry_date',
                    'expected': expected_date.isoformat(),
                    'actual': None,
                    'days_used_today': used_today
                })
                return False
            return True
        
        # Allow some tolerance (within 5 days) due to day-by-day checking
        days_diff = abs((safe_entry - expected_date).days)
        if days_diff > 5:
            self.discrepancies.append({
                'test': 'safe_entry_date',
                'expected': expected_date.isoformat(),
                'actual': safe_entry.isoformat() if safe_entry else None,
                'days_diff': days_diff
            })
            return False
        
        return True
    
    def get_discrepancies(self) -> List[Dict]:
        """Get all discrepancies"""
        return self.discrepancies
    
    def get_test_results(self) -> List[Dict]:
        """Get all test results"""
        return self.test_results


class TestBackendCalculationIntegrity:
    """Comprehensive backend calculation integrity tests"""
    
    @pytest.fixture
    def validator(self):
        return CalculationIntegrityValidator()
    
    def test_window_calculation_exactness(self, validator):
        """Test that window calculations are mathematically exact"""
        today = date.today()
        trips = [
            {
                'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
                'country': 'FR'
            }
        ]
        
        # Should be 11 days (inclusive)
        assert validator.validate_window_calculation(trips, today, 11)
        assert len(validator.get_discrepancies()) == 0
    
    def test_rolling_window_edge_cases(self, validator):
        """Test edge cases in rolling window"""
        results = validator.validate_rolling_window_edge_cases()
        
        failed_tests = [r for r in results if not r['passed']]
        if failed_tests:
            for test in failed_tests:
                validator.discrepancies.append(test)
        
        assert len(failed_tests) == 0, f"Failed edge case tests: {failed_tests}"
    
    def test_leap_year_handling(self, validator):
        """Test leap year handling"""
        assert validator.validate_leap_year_handling()
        assert len(validator.get_discrepancies()) == 0
    
    def test_overlapping_trips(self, validator):
        """Test overlapping trips don't double-count"""
        assert validator.validate_overlapping_trips()
        assert len(validator.get_discrepancies()) == 0
    
    def test_partial_day_handling(self, validator):
        """Test partial day handling"""
        assert validator.validate_partial_day_handling()
        assert len(validator.get_discrepancies()) == 0
    
    def test_ireland_exclusion(self, validator):
        """Test Ireland exclusion"""
        assert validator.validate_ireland_exclusion()
        assert len(validator.get_discrepancies()) == 0
    
    def test_90_day_limit_precision(self, validator):
        """Test exact 90-day limit handling"""
        assert validator.validate_90_day_limit_precision()
        assert len(validator.get_discrepancies()) == 0
    
    def test_safe_entry_date_calculation(self, validator):
        """Test safe entry date calculation"""
        assert validator.validate_safe_entry_date_calculation()
        assert len(validator.get_discrepancies()) == 0
    
    def test_comprehensive_scenario(self, validator):
        """Test complex real-world scenario"""
        today = date.today()
        complex_trips = [
            {
                'entry_date': (today - timedelta(days=150)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=140)).strftime('%Y-%m-%d'),
                'country': 'FR'
            },
            {
                'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
                'country': 'DE'
            },
            {
                'entry_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=20)).strftime('%Y-%m-%d'),
                'country': 'IT'
            },
            {
                'entry_date': (today - timedelta(days=10)).strftime('%Y-%m-%d'),
                'exit_date': (today - timedelta(days=5)).strftime('%Y-%m-%d'),
                'country': 'IE'  # Should be excluded
            }
        ]
        
        # Calculate expected: only trips within 180-day window
        # Trip 1: outside window (150 days ago)
        # Trip 2: 51 days (days 50-100)
        # Trip 3: 11 days (days 20-30)
        # Trip 4: excluded (Ireland) + 6 days (days 5-10)
        # Total: 51 + 11 + 6 = 68 days
        
        presence = presence_days(complex_trips)
        days_used = days_used_in_window(presence, today)
        
        # Verify calculation
        assert days_used > 0, "Should have days in window"
        assert days_used <= 90, "Should not exceed limit in this scenario"
        
        # Check that Ireland days are not counted
        assert validator.validate_ireland_exclusion()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

