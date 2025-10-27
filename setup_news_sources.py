#!/usr/bin/env python3
"""
Setup script to configure news sources for EU Trip Tracker
This script should be run after database initialization to set up proper news sources.
"""

import sqlite3
import os
from datetime import datetime

def setup_news_sources(db_path):
    """Set up news sources with working RSS feeds and sample data"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Clear existing sources and cache
    c.execute('DELETE FROM news_sources')
    c.execute('DELETE FROM news_cache')
    
    # Add working RSS feeds
    sources = [
        ('GOV.UK Foreign Travel', 'https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom', 1, 'Contains public-sector information licensed under the Open Government Licence v3.0.'),
        ('BBC News Europe', 'http://feeds.bbci.co.uk/news/world/europe/rss.xml', 1, None),
        ('Reuters Europe', 'https://feeds.reuters.com/reuters/europe', 1, None),
    ]
    
    c.executemany('INSERT INTO news_sources (name, url, enabled, license_note) VALUES (?, ?, ?, ?)', sources)
    
    # Add some sample EU-related news items for testing
    sample_news = [
        (1, 'Spain Travel Advice Updated', 'https://example.com/spain-travel', 'Updated travel advice for Spain including new entry requirements', datetime.now().isoformat(), datetime.now().isoformat()),
        (1, 'ETIAS System Implementation', 'https://example.com/etias', 'New ETIAS system will be implemented for visa-free travelers to the EU', datetime.now().isoformat(), datetime.now().isoformat()),
        (1, 'France Travel Restrictions', 'https://example.com/france-travel', 'Updated travel restrictions and requirements for France', datetime.now().isoformat(), datetime.now().isoformat()),
        (1, 'Schengen Visa Changes', 'https://example.com/schengen', 'Important updates to Schengen visa application process', datetime.now().isoformat(), datetime.now().isoformat()),
        (1, 'Germany Entry Requirements', 'https://example.com/germany', 'New entry requirements for travelers to Germany', datetime.now().isoformat(), datetime.now().isoformat()),
        (1, 'European Commission Travel Update', 'https://example.com/eu-commission', 'European Commission announces new travel policies for EU citizens', datetime.now().isoformat(), datetime.now().isoformat()),
    ]
    
    c.executemany('INSERT INTO news_cache (source_id, title, url, summary, published_at, fetched_at) VALUES (?, ?, ?, ?, ?, ?)', sample_news)
    
    conn.commit()
    print(f'✅ Added {len(sources)} news sources and {len(sample_news)} sample news items')
    
    # Verify the setup
    c.execute('SELECT COUNT(*) FROM news_sources WHERE enabled = 1')
    enabled_count = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM news_cache')
    cache_count = c.fetchone()[0]
    
    print(f'✅ Total enabled sources: {enabled_count}')
    print(f'✅ Total cached news items: {cache_count}')
    
    conn.close()

if __name__ == '__main__':
    # Determine database path
    db_path = os.getenv('DATABASE_PATH', 'data/eu_tracker.db')
    
    if not os.path.exists(db_path):
        print(f'❌ Database not found at {db_path}')
        print('Please run the application first to initialize the database.')
        exit(1)
    
    print(f'Setting up news sources for database: {db_path}')
    setup_news_sources(db_path)
    print('✅ News sources setup complete!')
