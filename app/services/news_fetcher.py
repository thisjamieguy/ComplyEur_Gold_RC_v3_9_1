"""
News Fetcher Service
Fetches EU travel news from RSS feeds and caches results in SQLite
"""

import feedparser
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import re

logger = logging.getLogger(__name__)

# EU27 + Iceland, Norway, Switzerland, Liechtenstein
EU_COUNTRIES = {
    "Austria": ["Austria"],
    "Belgium": ["Belgium"],
    "Bulgaria": ["Bulgaria"],
    "Croatia": ["Croatia"],
    "Cyprus": ["Cyprus"],
    "Czechia": ["Czechia", "Czech Republic"],
    "Denmark": ["Denmark"],
    "Estonia": ["Estonia"],
    "Finland": ["Finland"],
    "France": ["France"],
    "Germany": ["Germany"],
    "Greece": ["Greece", "Hellenic"],
    "Hungary": ["Hungary"],
    "Ireland": ["Ireland"],
    "Italy": ["Italy"],
    "Latvia": ["Latvia"],
    "Lithuania": ["Lithuania"],
    "Luxembourg": ["Luxembourg", "Luxemburg"],
    "Malta": ["Malta"],
    "Netherlands": ["Netherlands", "Holland"],
    "Poland": ["Poland"],
    "Portugal": ["Portugal"],
    "Romania": ["Romania"],
    "Slovakia": ["Slovakia"],
    "Slovenia": ["Slovenia"],
    "Spain": ["Spain"],
    "Sweden": ["Sweden"],
    "Iceland": ["Iceland"],
    "Norway": ["Norway"],
    "Switzerland": ["Switzerland"],
    "Liechtenstein": ["Liechtenstein"]
}

# EU-wide keywords for filtering
EU_KEYWORDS = [
    "schengen", "etias", "ees", "european commission", "eu", 
    "home affairs", "border checks", "visa waiver"
]

class NewsItem:
    """News item data structure"""
    def __init__(self, title: str, summary: str, tags: List[str] = None, categories: List[str] = None):
        self.title = title
        self.summary = summary
        self.tags = tags or []
        self.categories = categories or []
        self.matched_label = None

def should_keep_news(item: NewsItem) -> Tuple[bool, str]:
    """
    Determine if a news item should be kept based on EU/Schengen relevance.
    
    Args:
        item: NewsItem object with title, summary, tags, and categories
        
    Returns:
        Tuple of (should_keep: bool, matched_label: str)
    """
    # Concatenate all text content and convert to lowercase
    all_text = f"{item.title} {item.summary} {' '.join(item.tags)} {' '.join(item.categories)}".lower()
    
    # Check for EU-wide keywords
    for keyword in EU_KEYWORDS:
        if keyword.lower() in all_text:
            return True, "EU-wide"
    
    # Check for country names and aliases
    for country, aliases in EU_COUNTRIES.items():
        for alias in aliases:
            if alias.lower() in all_text:
                return True, country
    
    return False, ""

def filter_news_by_region(news_items: List[Dict], region_filter: str) -> List[Dict]:
    """
    Filter news items based on region setting.
    
    Args:
        news_items: List of news item dictionaries
        region_filter: "EU_ONLY" or "ALL"
        
    Returns:
        Filtered list of news items with matched_label added
    """
    if region_filter == "ALL":
        # Add empty matched_label for all items
        for item in news_items:
            item['matched_label'] = ""
        return news_items
    
    # Apply EU filtering
    filtered_items = []
    for item in news_items:
        # Create NewsItem object
        news_item = NewsItem(
            title=item.get('title', ''),
            summary=item.get('summary', ''),
            tags=[],  # RSS feeds typically don't have tags
            categories=[]  # RSS feeds typically don't have categories
        )
        
        should_keep, matched_label = should_keep_news(news_item)
        
        if should_keep:
            item['matched_label'] = matched_label
            filtered_items.append(item)
    
    return filtered_items

def fetch_news_from_sources(db_path: str, max_age_hours: int = 6) -> List[Dict]:
    """
    Fetch news from enabled sources and cache results.
    
    Args:
        db_path: Path to SQLite database
        max_age_hours: Maximum age of cached news before refetching
        
    Returns:
        List of news items from cache or fresh fetch
    """
    # Check if fetching is enabled
    if os.getenv('NEWS_FETCH_ENABLED', 'true').lower() == 'false':
        logger.info("News fetching is disabled via environment variable")
        return get_cached_news(db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Check cache freshness
        c.execute('SELECT MAX(fetched_at) FROM news_cache')
        result = c.fetchone()
        latest_fetch = result[0] if result[0] else None
        
        if latest_fetch:
            latest_fetch_dt = datetime.fromisoformat(latest_fetch)
            age = datetime.now() - latest_fetch_dt
            if age < timedelta(hours=max_age_hours):
                logger.info(f"Using cached news (age: {age})")
                return get_cached_news(db_path)
        
        # Fetch fresh news
        logger.info("Fetching fresh news from sources...")
        
        # Get enabled sources
        c.execute('SELECT id, name, url, license_note FROM news_sources WHERE enabled = 1')
        sources = c.fetchall()
        
        all_news = []
        
        for source in sources:
            try:
                logger.info(f"Fetching from {source['name']}...")
                feed = feedparser.parse(source['url'])
                
                for entry in feed.entries[:10]:  # Limit to 10 per source
                    # Extract or create summary
                    summary = entry.get('summary', entry.get('description', ''))
                    # Truncate to 200 chars
                    if len(summary) > 200:
                        summary = summary[:200] + '...'
                    
                    # Parse published date
                    published_at = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published_at = datetime(*entry.updated_parsed[:6])
                    
                    if not published_at:
                        published_at = datetime.now()
                    
                    news_item = {
                        'source_id': source['id'],
                        'source_name': source['name'],
                        'title': entry.get('title', 'No title'),
                        'url': entry.get('link', '#'),
                        'published_at': published_at,
                        'summary': summary,
                        'license_note': source['license_note']
                    }
                    all_news.append(news_item)
                    
                    # Cache in database
                    c.execute('''
                        INSERT OR REPLACE INTO news_cache 
                        (source_id, title, url, published_at, summary, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        source['id'],
                        news_item['title'],
                        news_item['url'],
                        news_item['published_at'].isoformat(),
                        news_item['summary'],
                        datetime.now().isoformat()
                    ))
                    
            except Exception as e:
                logger.error(f"Error fetching from {source['name']}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Fetched {len(all_news)} news items")
        
        # Apply region filtering
        region_filter = os.getenv('NEWS_FILTER_REGION', 'EU_ONLY')
        filtered_news = filter_news_by_region(all_news, region_filter)
        
        # Return sorted by published date (newest first)
        filtered_news.sort(key=lambda x: x['published_at'], reverse=True)
        return filtered_news[:15]  # Return top 15
        
    finally:
        conn.close()

def get_cached_news(db_path: str, limit: int = 15) -> List[Dict]:
    """
    Get news from cache only (no network requests).
    
    Args:
        db_path: Path to SQLite database
        limit: Maximum number of items to return
        
    Returns:
        List of cached news items
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT 
                nc.*,
                ns.name as source_name,
                ns.license_note
            FROM news_cache nc
            JOIN news_sources ns ON nc.source_id = ns.id
            ORDER BY nc.published_at DESC
            LIMIT ?
        ''', (limit,))
        
        rows = c.fetchall()
        
        news_items = []
        for row in rows:
            news_items.append({
                'source_name': row['source_name'],
                'title': row['title'],
                'url': row['url'],
                'published_at': datetime.fromisoformat(row['published_at']) if row['published_at'] else None,
                'summary': row['summary'],
                'license_note': row['license_note']
            })
        
        # Apply region filtering
        region_filter = os.getenv('NEWS_FILTER_REGION', 'EU_ONLY')
        filtered_news = filter_news_by_region(news_items, region_filter)
        
        return filtered_news
        
    finally:
        conn.close()

def clear_old_news(db_path: str, days_to_keep: int = 7):
    """
    Clear news items older than specified days.
    
    Args:
        db_path: Path to SQLite database
        days_to_keep: Number of days to keep news items
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        c.execute('DELETE FROM news_cache WHERE published_at < ?', (cutoff_date.isoformat(),))
        deleted_count = c.rowcount
        conn.commit()
        logger.info(f"Cleared {deleted_count} old news items")
    finally:
        conn.close()
