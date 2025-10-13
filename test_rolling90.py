"""
Unit tests for rolling90.py module

Tests the 90/180 day Schengen rule calculations
"""

import unittest
from datetime import date, timedelta
from app.services.rolling90 import (
    presence_days,
    days_used_in_window,
    earliest_safe_entry,
    calculate_days_remaining,
    get_risk_level
)


class TestPresenceDays(unittest.TestCase):
    """Test presence_days function"""
    
    def test_single_trip(self):
        """Test single trip returns correct days"""
        trips = [{'entry_date': '2024-01-01', 'exit_date': '2024-01-05', 'country': 'France'}]
        days = presence_days(trips)
        self.assertEqual(len(days), 5)  # 5 days inclusive
        
    def test_multiple_trips(self):
        """Test multiple non-overlapping trips"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-05', 'country': 'France'},
            {'entry_date': '2024-02-01', 'exit_date': '2024-02-03', 'country': 'Germany'}
        ]
        days = presence_days(trips)
        self.assertEqual(len(days), 8)  # 5 + 3 days
        
    def test_overlapping_trips(self):
        """Test overlapping trips don't double count"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-10', 'country': 'France'},
            {'entry_date': '2024-01-05', 'exit_date': '2024-01-15', 'country': 'Germany'}
        ]
        days = presence_days(trips)
        self.assertEqual(len(days), 15)  # 1st to 15th = 15 days
        
    def test_touching_trips(self):
        """Test trips that touch but don't overlap"""
        trips = [
            {'entry_date': '2024-01-01', 'exit_date': '2024-01-05', 'country': 'France'},
            {'entry_date': '2024-01-06', 'exit_date': '2024-01-10', 'country': 'Germany'}
        ]
        days = presence_days(trips)
        self.assertEqual(len(days), 10)  # 10 consecutive days
        
    def test_empty_trips(self):
        """Test empty trip list"""
        trips = []
        days = presence_days(trips)
        self.assertEqual(len(days), 0)


class TestDaysUsedInWindow(unittest.TestCase):
    """Test days_used_in_window function"""
    
    def test_all_days_in_window(self):
        """Test when all days are within window"""
        # Create 30 days recent enough to be in window
        ref_date = date(2024, 6, 30)
        # Start from 30 days ago so all are definitely in window
        presence = {ref_date - timedelta(days=i) for i in range(30)}
        used = days_used_in_window(presence, ref_date)
        self.assertEqual(used, 30)
        
    def test_some_days_outside_window(self):
        """Test when some days fall outside window"""
        presence = {date(2023, 1, 1) + timedelta(days=i) for i in range(30)}
        ref_date = date(2024, 6, 30)
        used = days_used_in_window(presence, ref_date)
        self.assertEqual(used, 0)  # All days too old
        
    def test_exact_window_boundary(self):
        """Test days at exact window boundaries"""
        ref_date = date(2024, 6, 30)
        window_start = ref_date - timedelta(days=179)  # 180 days ago
        presence = {window_start, ref_date}
        used = days_used_in_window(presence, ref_date)
        self.assertEqual(used, 2)
        
    def test_empty_presence(self):
        """Test empty presence set"""
        presence = set()
        ref_date = date(2024, 6, 30)
        used = days_used_in_window(presence, ref_date)
        self.assertEqual(used, 0)


class TestEarliestSafeEntry(unittest.TestCase):
    """Test earliest_safe_entry function"""
    
    def test_already_eligible(self):
        """Test when employee is already eligible"""
        presence = {date(2024, 1, 1) + timedelta(days=i) for i in range(30)}
        today = date(2024, 6, 30)
        safe_entry = earliest_safe_entry(presence, today)
        self.assertIsNone(safe_entry)  # Already eligible
        
    def test_at_limit(self):
        """Test when at exactly 90 days"""
        today = date(2024, 6, 30)
        presence = {today - timedelta(days=i) for i in range(90)}
        safe_entry = earliest_safe_entry(presence, today)
        self.assertIsNotNone(safe_entry)
        self.assertGreater(safe_entry, today)
        
    def test_over_limit(self):
        """Test when over 90 days"""
        today = date(2024, 6, 30)
        # Use 100 days in the window
        presence = {today - timedelta(days=i) for i in range(100)}
        safe_entry = earliest_safe_entry(presence, today)
        self.assertIsNotNone(safe_entry)
        # Should be when oldest days fall out
        self.assertGreater(safe_entry, today)
        
    def test_edge_case_89_days(self):
        """Test edge case with exactly 89 days"""
        today = date(2024, 6, 30)
        presence = {today - timedelta(days=i) for i in range(89)}
        safe_entry = earliest_safe_entry(presence, today)
        self.assertIsNone(safe_entry)  # 89 days = safe to enter
        
    def test_continuous_presence(self):
        """Test continuous 180-day presence"""
        today = date(2024, 6, 30)
        presence = {today - timedelta(days=i) for i in range(180)}
        safe_entry = earliest_safe_entry(presence, today)
        self.assertIsNotNone(safe_entry)
        # Should need to wait for oldest days to fall out


class TestCalculateDaysRemaining(unittest.TestCase):
    """Test calculate_days_remaining function"""
    
    def test_no_days_used(self):
        """Test with no days used"""
        presence = set()
        ref_date = date(2024, 6, 30)
        remaining = calculate_days_remaining(presence, ref_date)
        self.assertEqual(remaining, 90)
        
    def test_some_days_used(self):
        """Test with some days used"""
        # Create 30 days within the window
        ref_date = date(2024, 6, 30)
        presence = {ref_date - timedelta(days=i) for i in range(30)}
        remaining = calculate_days_remaining(presence, ref_date)
        self.assertEqual(remaining, 60)
        
    def test_at_limit(self):
        """Test at exactly 90 days"""
        today = date(2024, 6, 30)
        presence = {today - timedelta(days=i) for i in range(90)}
        remaining = calculate_days_remaining(presence, today)
        self.assertEqual(remaining, 0)
        
    def test_over_limit(self):
        """Test over limit returns negative"""
        today = date(2024, 6, 30)
        presence = {today - timedelta(days=i) for i in range(100)}
        remaining = calculate_days_remaining(presence, today)
        self.assertEqual(remaining, -10)


class TestGetRiskLevel(unittest.TestCase):
    """Test get_risk_level function"""
    
    def test_green_threshold(self):
        """Test green risk level"""
        thresholds = {'green': 30, 'amber': 10}
        self.assertEqual(get_risk_level(35, thresholds), 'green')
        self.assertEqual(get_risk_level(30, thresholds), 'green')
        
    def test_amber_threshold(self):
        """Test amber risk level"""
        thresholds = {'green': 30, 'amber': 10}
        self.assertEqual(get_risk_level(29, thresholds), 'amber')
        self.assertEqual(get_risk_level(15, thresholds), 'amber')
        self.assertEqual(get_risk_level(10, thresholds), 'amber')
        
    def test_red_threshold(self):
        """Test red risk level"""
        thresholds = {'green': 30, 'amber': 10}
        self.assertEqual(get_risk_level(9, thresholds), 'red')
        self.assertEqual(get_risk_level(0, thresholds), 'red')
        self.assertEqual(get_risk_level(-5, thresholds), 'red')


class TestRolling90EdgeCases(unittest.TestCase):
    """Test edge cases and complex scenarios"""
    
    def test_gap_in_presence(self):
        """Test gap in presence doesn't affect calculation"""
        today = date(2024, 6, 30)
        # Create trips that are definitely within the 180-day window
        trips = [
            {'entry_date': '2024-05-01', 'exit_date': '2024-05-10', 'country': 'France'},
            {'entry_date': '2024-06-01', 'exit_date': '2024-06-10', 'country': 'Germany'}
        ]
        presence = presence_days(trips)
        used = days_used_in_window(presence, today)
        self.assertEqual(used, 20)  # Both trips in window (10 days each)
        
    def test_trip_spanning_window_boundary(self):
        """Test trip that spans window boundary"""
        today = date(2024, 6, 30)
        window_start = today - timedelta(days=179)
        # Trip starts before window, ends in window
        trips = [{
            'entry_date': (window_start - timedelta(days=10)).strftime('%Y-%m-%d'),
            'exit_date': (window_start + timedelta(days=10)).strftime('%Y-%m-%d'),
            'country': 'France'
        }]
        presence = presence_days(trips)
        used = days_used_in_window(presence, today)
        # Should only count days within window (11 days)
        self.assertEqual(used, 11)
        
    def test_current_trip(self):
        """Test calculation with current ongoing trip"""
        today = date(2024, 6, 30)
        trips = [{
            'entry_date': '2024-06-20',
            'exit_date': '2024-07-10',  # Future end date
            'country': 'France'
        }]
        presence = presence_days(trips)
        used = days_used_in_window(presence, today)
        # Should count 20-30 June = 11 days
        self.assertEqual(used, 11)


if __name__ == '__main__':
    unittest.main()

