"""
Unit tests for rolling 90/180 day logic
"""

import pytest
from datetime import date, timedelta
from app.services.rolling90 import (
    presence_days, days_used_in_window, earliest_safe_entry,
    calculate_days_remaining, get_risk_level, days_until_compliant,
    is_schengen_country
)


class TestSchengenCountryDetection:
    def test_schengen_countries(self):
        """Test that Schengen countries are correctly identified"""
        assert is_schengen_country('FR') == True
        assert is_schengen_country('DE') == True
        assert is_schengen_country('IT') == True
        assert is_schengen_country('Spain') == True
        assert is_schengen_country('France') == True
    
    def test_ireland_exclusion(self):
        """Test that Ireland is correctly excluded from Schengen"""
        assert is_schengen_country('IE') == False
        assert is_schengen_country('Ireland') == False
        assert is_schengen_country('ireland') == False
    
    def test_invalid_countries(self):
        """Test handling of invalid country inputs"""
        assert is_schengen_country('') is False
        assert is_schengen_country(None) is False
        assert is_schengen_country('XX') is False
        assert is_schengen_country('United Kingdom') is False


class TestPresenceDays:
    def test_single_trip(self):
        """Test presence days calculation for a single trip"""
        trips = [{
            'entry_date': '2024-01-01',
            'exit_date': '2024-01-05',
            'country': 'FR'
        }]
        days = presence_days(trips)
        expected = {date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4), date(2024, 1, 5)}
        assert days == expected
    
    def test_multiple_trips(self):
        """Test presence days calculation for multiple trips"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-03', 'country': 'FR'},
            {'entry_date': '2024-01-10', 'exit_date': '2024-01-12', 'country': 'DE'}
        ]
        days = presence_days(trips)
        expected = {
            date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3),
            date(2024, 1, 10), date(2024, 1, 11), date(2024, 1, 12)
        }
        assert days == expected
    
    def test_ireland_exclusion(self):
        """Test that Ireland trips are excluded from presence days"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-03', 'country': 'FR'},
            {'entry_date': '2024-01-10', 'exit_date': '2024-01-12', 'country': 'IE'}
        ]
        days = presence_days(trips)
        expected = {date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)}
        assert days == expected


class TestDaysUsedInWindow:
    def test_no_trips_in_window(self):
        """Test when no trips fall within the 180-day window"""
        trips = [{'entry_date': '2020-01-01', 'exit_date': '2020-01-05', 'country': 'FR'}]
        presence = presence_days(trips)
        ref_date = date(2024, 1, 1)
        days_used = days_used_in_window(presence, ref_date)
        assert days_used == 0
    
    def test_trips_in_window(self):
        """Test when trips fall within the 180-day window"""
        today = date(2024, 1, 1)
        trips = [
            {'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'country': 'FR'},
            {'entry_date': (today - timedelta(days=50)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=40)).strftime('%Y-%m-%d'),
            'country': 'DE'}
        ]
        presence = presence_days(trips)
        days_used = days_used_in_window(presence, today)
        assert days_used == 22  # 11 days + 11 days
    
    def test_edge_case_window_boundary(self):
        """Test trips exactly at the window boundary"""
        today = date(2024, 1, 1)
        window_start = today - timedelta(days=180)
        window_end = today - timedelta(days=1)
        
        trips = [
            {'entry_date': window_start.strftime('%Y-%m-%d'),
            'exit_date': window_start.strftime('%Y-%m-%d'),
            'country': 'FR'},
            {'entry_date': window_end.strftime('%Y-%m-%d'),
            'exit_date': window_end.strftime('%Y-%m-%d'),
            'country': 'DE'}
        ]
        presence = presence_days(trips)
        days_used = days_used_in_window(presence, today)
        assert days_used == 2


class TestRiskLevel:
    def test_risk_levels(self):
        """Test risk level calculation"""
        thresholds = {'green': 30, 'amber': 10}
        
        assert get_risk_level(35, thresholds) == 'green'
        assert get_risk_level(30, thresholds) == 'green'
        assert get_risk_level(15, thresholds) == 'amber'
        assert get_risk_level(10, thresholds) == 'amber'
        assert get_risk_level(5, thresholds) == 'red'
        assert get_risk_level(0, thresholds) == 'red'
        assert get_risk_level(-5, thresholds) == 'red'


class TestEarliestSafeEntry:
    def test_already_eligible(self):
        """Test when employee is already eligible"""
        trips = [{'entry_date': '2020-01-01', 'exit_date': '2020-01-05', 'country': 'FR'}]
        presence = presence_days(trips)
        today = date(2024, 1, 1)
        safe_entry = earliest_safe_entry(presence, today)
        assert safe_entry is None  # Already eligible
    
    def test_needs_wait(self):
        """Test when employee needs to wait"""
        today = date(2024, 1, 1)
        # Create a trip that uses 90 days
        trips = [{
            'entry_date': (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        presence = presence_days(trips)
        safe_entry = earliest_safe_entry(presence, today)
        assert safe_entry is not None
        assert safe_entry > today


class TestDaysUntilCompliant:
    def test_already_compliant(self):
        """Test when employee is already compliant"""
        trips = [{'entry_date': '2020-01-01', 'exit_date': '2020-01-05', 'country': 'FR'}]
        presence = presence_days(trips)
        today = date(2024, 1, 1)
        days_until, compliance_date = days_until_compliant(presence, today)
        assert days_until == 0
        assert compliance_date == today
    
    def test_over_limit(self):
        """Test when employee is over the limit"""
        today = date(2024, 1, 1)
        # Create a trip that uses 100 days (10 over limit)
        trips = [{
            'entry_date': (today - timedelta(days=100)).strftime('%Y-%m-%d'),
            'exit_date': (today - timedelta(days=1)).strftime('%Y-%m-%d'),
            'country': 'FR'
        }]
        presence = presence_days(trips)
        days_until, compliance_date = days_until_compliant(presence, today)
        assert days_until > 0
        assert compliance_date > today


class TestEdgeCases:
    def test_overlapping_trips(self):
        """Test handling of overlapping trips"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-10', 'country': 'FR'},
            {'entry_date': '2024-01-05', 'exit_date': '2024-01-15', 'country': 'DE'}
        ]
        presence = presence_days(trips)
        # Should not double-count overlapping days
        assert len(presence) == 15  # Jan 1-15 inclusive
    
    def test_same_day_entry_exit(self):
        """Test same-day entry and exit"""
        trips = [{'entry_date': '2024-01-01', 'exit_date': '2024-01-01', 'country': 'FR'}]
        presence = presence_days(trips)
        assert presence == {date(2024, 1, 1)}
    
    def test_cross_month_boundary(self):
        """Test trips that cross month boundaries"""
        trips = [{'entry_date': '2024-01-30', 'exit_date': '2024-02-02', 'country': 'FR'}]
        presence = presence_days(trips)
        expected = {date(2024, 1, 30), date(2024, 1, 31), date(2024, 2, 1), date(2024, 2, 2)}
        assert presence == expected
