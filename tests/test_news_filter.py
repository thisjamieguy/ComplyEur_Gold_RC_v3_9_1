"""
Unit tests for news filtering functionality
"""

import unittest
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.news_fetcher import should_keep_news, NewsItem, filter_news_by_region


class TestNewsFilter(unittest.TestCase):
    """Test cases for news filtering functionality"""
    
    def test_should_keep_news_eu_keywords(self):
        """Test that EU-wide keywords are detected correctly"""
        # Test positive cases
        test_cases = [
            ("ETIAS update for travelers", "New ETIAS requirements", [], []),
            ("Schengen visa changes", "Important updates", [], []),
            ("EES system implementation", "Border control updates", [], []),
            ("European Commission announcement", "Policy changes", [], []),
            ("EU travel regulations", "New rules", [], []),
            ("Home Affairs update", "Security measures", [], []),
            ("Border checks enhanced", "New procedures", [], []),
            ("Visa waiver program", "Updated requirements", [], [])
        ]
        
        for title, summary, tags, categories in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertTrue(should_keep, f"Should keep news with title: {title}")
                self.assertEqual(matched_label, "EU-wide", f"Should match EU-wide for: {title}")
    
    def test_should_keep_news_country_names(self):
        """Test that EU country names are detected correctly"""
        # Test positive cases for various countries
        test_cases = [
            ("Spain travel advice", "Updated travel information", [], [], "Spain"),
            ("France travel restrictions", "New requirements", [], [], "France"),
            ("Germany entry requirements", "Updated rules", [], [], "Germany"),
            ("Italy travel updates", "New information", [], [], "Italy"),
            ("Netherlands travel advice", "Updated guidance", [], [], "Netherlands"),
            ("Holland travel information", "New updates", [], [], "Netherlands"),  # Alias
            ("Czech Republic travel", "Updated advice", [], [], "Czechia"),
            ("Czechia travel updates", "New information", [], [], "Czechia"),  # Alias
            ("Greece travel advice", "Updated guidance", [], [], "Greece"),
            ("Hellenic travel updates", "New information", [], [], "Greece"),  # Alias
            ("Luxembourg travel", "Updated advice", [], [], "Luxembourg"),
            ("Luxemburg travel updates", "New information", [], [], "Luxembourg"),  # Alias
        ]
        
        for title, summary, tags, categories, expected_country in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertTrue(should_keep, f"Should keep news with title: {title}")
                self.assertEqual(matched_label, expected_country, f"Should match {expected_country} for: {title}")
    
    def test_should_keep_news_case_insensitive(self):
        """Test that filtering is case-insensitive"""
        test_cases = [
            ("SPAIN TRAVEL ADVICE", "Updated information", [], []),
            ("france travel restrictions", "New requirements", [], []),
            ("Etias Update", "New system", [], []),
            ("SCHENGEN VISA", "Updated rules", [], []),
        ]
        
        for title, summary, tags, categories in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertTrue(should_keep, f"Should keep news with title: {title} (case insensitive)")
    
    def test_should_keep_news_unicode_safe(self):
        """Test that filtering works with unicode characters"""
        test_cases = [
            ("Spain travel advice", "Información actualizada", [], []),  # English country name with unicode summary
            ("France travel updates", "Nouvelles informations", [], []),  # English country name with unicode summary
            ("Germany travel", "Aktualisierte Informationen", [], []),  # English country name with unicode summary
            ("ETIAS update", "Información actualizada", [], []),  # EU keyword with unicode summary
        ]
        
        for title, summary, tags, categories in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertTrue(should_keep, f"Should keep news with unicode content: {title}")
    
    def test_should_keep_news_negative_cases(self):
        """Test that non-EU content is filtered out"""
        test_cases = [
            ("Mauritania travel advice", "Updated information", [], []),
            ("Japan travel restrictions", "New requirements", [], []),
            ("Australia travel updates", "New information", [], []),
            ("Brazil travel advice", "Updated guidance", [], []),
            ("India travel information", "New updates", [], []),
            ("China travel requirements", "Updated rules", [], []),
            ("General travel tips", "Helpful advice", [], []),
            ("Weather updates", "Climate information", [], []),
        ]
        
        for title, summary, tags, categories in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertFalse(should_keep, f"Should NOT keep news with title: {title}")
                self.assertEqual(matched_label, "", f"Should have empty matched_label for: {title}")
    
    def test_should_keep_news_mixed_content(self):
        """Test news items with mixed content (EU and non-EU)"""
        test_cases = [
            ("Global travel update including Spain and France", "Worldwide travel information", [], [], True),
            ("EU and US travel regulations", "International updates", [], [], True),
            ("Schengen and UK travel advice", "European travel information", [], [], True),
        ]
        
        for title, summary, tags, categories, should_keep_expected in test_cases:
            with self.subTest(title=title):
                item = NewsItem(title, summary, tags, categories)
                should_keep, matched_label = should_keep_news(item)
                self.assertEqual(should_keep, should_keep_expected, f"Unexpected result for: {title}")
                if should_keep_expected:
                    self.assertNotEqual(matched_label, "", f"Should have matched_label for: {title}")
    
    def test_filter_news_by_region_eu_only(self):
        """Test filtering with EU_ONLY setting"""
        news_items = [
            {"title": "Spain travel advice", "summary": "Updated information", "source_name": "GOV.UK"},
            {"title": "Mauritania travel advice", "summary": "Updated information", "source_name": "GOV.UK"},
            {"title": "ETIAS update", "summary": "New requirements", "source_name": "EU News"},
        ]
        
        filtered = filter_news_by_region(news_items, "EU_ONLY")
        
        # Should only keep EU-relevant items
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["title"], "Spain travel advice")
        self.assertEqual(filtered[0]["matched_label"], "Spain")
        self.assertEqual(filtered[1]["title"], "ETIAS update")
        self.assertEqual(filtered[1]["matched_label"], "EU-wide")
    
    def test_filter_news_by_region_all(self):
        """Test filtering with ALL setting"""
        news_items = [
            {"title": "Spain travel advice", "summary": "Updated information", "source_name": "GOV.UK"},
            {"title": "Mauritania travel advice", "summary": "Updated information", "source_name": "GOV.UK"},
            {"title": "ETIAS update", "summary": "New requirements", "source_name": "EU News"},
        ]
        
        filtered = filter_news_by_region(news_items, "ALL")
        
        # Should keep all items with empty matched_label
        self.assertEqual(len(filtered), 3)
        for item in filtered:
            self.assertEqual(item["matched_label"], "")


if __name__ == '__main__':
    unittest.main()
