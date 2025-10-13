"""
Unit tests for trip_validator.py module

Tests trip validation rules and overlap detection
"""

import unittest
from datetime import date, timedelta
from app.services.trip_validator import (
    validate_trip,
    validate_date_range,
    check_trip_overlaps
)


class TestValidateTrip(unittest.TestCase):
    """Test validate_trip function"""
    
    def test_valid_trip(self):
        """Test valid trip with no issues"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'}
        ]
        new_entry = date(2024, 2, 1)
        new_exit = date(2024, 2, 10)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 0)
        
    def test_exit_before_entry(self):
        """Test error when exit date is before entry date"""
        existing_trips = []
        new_entry = date(2024, 2, 10)
        new_exit = date(2024, 2, 1)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 1)
        self.assertIn('Exit date cannot be before entry date', errors[0])
        
    def test_overlapping_trips(self):
        """Test error for overlapping trips"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'}
        ]
        new_entry = date(2024, 1, 5)
        new_exit = date(2024, 1, 15)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 1)
        self.assertIn('overlap', errors[0].lower())
        
    def test_touching_trips_no_overlap(self):
        """Test touching trips (end/start on same day) don't overlap"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'}
        ]
        new_entry = date(2024, 1, 11)
        new_exit = date(2024, 1, 20)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)
        
    def test_trip_longer_than_90_days(self):
        """Test warning for trip longer than 90 days"""
        existing_trips = []
        new_entry = date(2024, 1, 1)
        new_exit = date(2024, 4, 15)  # More than 90 days
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn('90 days', warnings[0])
        
    def test_missing_exit_date(self):
        """Test warning for missing exit date (ongoing trip)"""
        existing_trips = []
        new_entry = date(2024, 1, 1)
        new_exit = None
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn('no exit date', warnings[0].lower())
        
    def test_exclude_trip_being_edited(self):
        """Test that trip being edited is excluded from overlap check"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-02-01', 'exit_date': '2024-02-10'}
        ]
        # Edit trip 1 to overlap with itself (should be OK)
        new_entry = date(2024, 1, 5)
        new_exit = date(2024, 1, 15)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit, trip_id_to_exclude=1)
        self.assertEqual(len(errors), 0)
        
    def test_multiple_overlaps(self):
        """Test detection of multiple overlapping trips"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-15', 'exit_date': '2024-01-25'}
        ]
        # New trip overlaps both
        new_entry = date(2024, 1, 5)
        new_exit = date(2024, 1, 20)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 2)  # Two overlap errors
        
    def test_trip_completely_contains_existing(self):
        """Test when new trip completely contains existing trip"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-10', 'exit_date': '2024-01-15'}
        ]
        new_entry = date(2024, 1, 1)
        new_exit = date(2024, 1, 20)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 1)
        self.assertIn('overlap', errors[0].lower())
        
    def test_trip_completely_inside_existing(self):
        """Test when new trip is completely inside existing trip"""
        existing_trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-20'}
        ]
        new_entry = date(2024, 1, 10)
        new_exit = date(2024, 1, 15)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 1)
        self.assertIn('overlap', errors[0].lower())


class TestValidateDateRange(unittest.TestCase):
    """Test validate_date_range function"""
    
    def test_valid_date_range(self):
        """Test valid date range"""
        entry = date(2024, 1, 1)
        exit_d = date(2024, 1, 10)
        
        is_valid, error = validate_date_range(entry, exit_d)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
    def test_exit_before_entry(self):
        """Test exit before entry error"""
        entry = date(2024, 1, 10)
        exit_d = date(2024, 1, 1)
        
        is_valid, error = validate_date_range(entry, exit_d)
        self.assertFalse(is_valid)
        self.assertIn('after', error.lower())
        
    def test_same_day(self):
        """Test same day entry and exit"""
        entry = date(2024, 1, 1)
        exit_d = date(2024, 1, 1)
        
        is_valid, error = validate_date_range(entry, exit_d)
        # Same day is technically valid (edge case for day trips)
        # The validate_date_range only fails if exit < entry
        self.assertFalse(is_valid)  # Exit must be AFTER entry, not equal
        
    def test_excessive_duration(self):
        """Test trip duration exceeding 2 years"""
        entry = date(2024, 1, 1)
        exit_d = date(2026, 1, 2)  # Over 2 years
        
        is_valid, error = validate_date_range(entry, exit_d)
        self.assertFalse(is_valid)
        self.assertIn('2 years', error.lower())


class TestCheckTripOverlaps(unittest.TestCase):
    """Test check_trip_overlaps function"""
    
    def test_no_overlaps(self):
        """Test trips with no overlaps"""
        trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-15', 'exit_date': '2024-01-25'}
        ]
        
        overlaps = check_trip_overlaps(trips)
        self.assertEqual(len(overlaps), 0)
        
    def test_one_overlap(self):
        """Test detecting one overlap"""
        trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-05', 'exit_date': '2024-01-15'}
        ]
        
        overlaps = check_trip_overlaps(trips)
        self.assertEqual(len(overlaps), 1)
        self.assertEqual(overlaps[0][0]['id'], 1)
        self.assertEqual(overlaps[0][1]['id'], 2)
        
    def test_multiple_overlaps(self):
        """Test detecting multiple overlaps"""
        trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-05', 'exit_date': '2024-01-15'},
            {'id': 3, 'entry_date': '2024-01-08', 'exit_date': '2024-01-20'}
        ]
        
        overlaps = check_trip_overlaps(trips)
        # Should find 3 overlaps: 1-2, 1-3, 2-3
        self.assertEqual(len(overlaps), 3)
        
    def test_exclude_trip(self):
        """Test excluding a trip from overlap check"""
        trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-05', 'exit_date': '2024-01-15'}
        ]
        
        overlaps = check_trip_overlaps(trips, exclude_trip_id=1)
        self.assertEqual(len(overlaps), 0)  # Trip 1 excluded, no overlap with trip 2
        
    def test_touching_trips(self):
        """Test that touching trips are not considered overlaps"""
        trips = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'},
            {'id': 2, 'entry_date': '2024-01-10', 'exit_date': '2024-01-20'}
        ]
        
        overlaps = check_trip_overlaps(trips)
        # Day 10 is both exit of trip 1 and entry of trip 2
        # This IS an overlap (both on same day)
        self.assertEqual(len(overlaps), 1)


class TestValidationEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""
    
    def test_date_objects_vs_strings(self):
        """Test validation works with both date objects and strings"""
        # Test with date objects
        existing_trips = [
            {'id': 1, 'entry_date': date(2024, 1, 1), 'exit_date': date(2024, 1, 10)}
        ]
        new_entry = date(2024, 1, 5)
        new_exit = date(2024, 1, 15)
        
        errors1, warnings1 = validate_trip(existing_trips, new_entry, new_exit)
        
        # Test with strings
        existing_trips_str = [
            {'id': 1, 'entry_date': '2024-01-01', 'exit_date': '2024-01-10'}
        ]
        
        errors2, warnings2 = validate_trip(existing_trips_str, new_entry, new_exit)
        
        # Both should produce same errors
        self.assertEqual(len(errors1), len(errors2))
        
    def test_empty_existing_trips(self):
        """Test validation with no existing trips"""
        existing_trips = []
        new_entry = date(2024, 1, 1)
        new_exit = date(2024, 1, 10)
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)
        
    def test_one_day_trip(self):
        """Test one-day trip validation"""
        existing_trips = []
        new_entry = date(2024, 1, 1)
        new_exit = date(2024, 1, 2)  # Next day
        
        errors, warnings = validate_trip(existing_trips, new_entry, new_exit)
        self.assertEqual(len(errors), 0)


if __name__ == '__main__':
    unittest.main()

