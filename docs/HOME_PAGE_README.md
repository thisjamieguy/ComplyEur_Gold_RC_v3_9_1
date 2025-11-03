# Home Screen Feature - v1.5.2

## Overview

The home screen is the first page users see after logging in, providing quick access to key statistics and the latest EU travel news.

## Features

### 1. Quick Info Cards

Three dashboard cards display:
- **Active Employees**: Total number of employees in the system
- **Trips Logged This Month**: Count of trips logged in the current month
- **At Risk of 90-Day Limit**: Employees with less than 10 days remaining in their 90-day EU allowance

### 2. EU Travel News Feed

Automatically fetches and displays the latest news from:
- GOV.UK Foreign Travel Advice (Open Government Licence v3.0)
- EU Home Affairs News
- SchengenVisaInfo

## Technical Implementation

### Database Schema

#### news_sources table
```sql
CREATE TABLE news_sources (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    license_note TEXT
);
```

#### news_cache table
```sql
CREATE TABLE news_cache (
    id INTEGER PRIMARY KEY,
    source_id INTEGER,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    published_at DATETIME,
    summary TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES news_sources (id)
);
```

### News Fetching

The system uses the `feedparser` library to fetch RSS feeds from configured sources. News is cached in SQLite for 6 hours to avoid repeated requests.

**Service Location**: `app/services/news_fetcher.py`

**Key Functions**:
- `fetch_news_from_sources()`: Fetches news from all enabled sources
- `get_cached_news()`: Retrieves cached news without network requests
- `clear_old_news()`: Removes news older than specified days

### Routes

- `/home`: Home page route (redirected to after login)
- `/dashboard`: Original dashboard (still accessible from sidebar)

### Environment Variables

- `NEWS_FETCH_ENABLED`: Set to `false` to disable news fetching (default: `true`)

## Usage

### Automatic News Refresh

News is automatically fetched when:
1. Cache is older than 6 hours
2. User visits the home page
3. Cache is empty

### Manual News Fetch

To manually refresh news (CLI command):
```bash
flask news-fetch
```

To add this command, add the following to your Flask app:

```python
import click
from app.services.news_fetcher import fetch_news_from_sources, clear_old_news
from flask import current_app

@click.command('news-fetch')
def news_fetch():
    """Fetch fresh news from RSS feeds"""
    with app.app_context():
        db_path = current_app.config['DATABASE']
        items = fetch_news_from_sources(db_path)
        click.echo(f"Fetched {len(items)} news items")
        
        # Clean up old news (older than 7 days)
        clear_old_news(db_path, days_to_keep=7)
        click.echo("Cleaned up old news items")

app.cli.add_command(news_fetch)
```

## Customization

### Adding News Sources

To add a new news source, insert into the `news_sources` table:

```sql
INSERT INTO news_sources (name, url, enabled, license_note)
VALUES ('Source Name', 'https://example.com/feed.xml', 1, 'Optional license note');
```

### Modifying Cache Duration

Edit `app/services/news_fetcher.py`:

```python
news_items = fetch_news_from_sources(db_path, max_age_hours=12)  # Change from 6 to 12 hours
```

### Styling

The home page uses inline styles matching the ComplyEur theme:
- Primary Blue: `#2563eb`
- Success Green: `#10b981`
- Danger Red: `#ef4444`
- Background: `var(--base-bg)`

Modify `app/templates/home.html` for custom styling.

## GDPR Compliance

- No personal data is collected or stored
- Only public news headlines and links are cached
- Full attribution provided for GOV.UK content
- Content cached for 7 days maximum (configurable)

## Troubleshooting

### News Not Loading

1. Check `NEWS_FETCH_ENABLED` environment variable
2. Verify internet connectivity
3. Check logs for RSS fetch errors
4. Review database for cached news

### Slow Page Load

1. News fetching happens on first visit
2. Subsequent visits use cached data (fast)
3. Consider disabling news fetching if on slow networks

## Version History

- **v1.5.2**: Initial home page implementation with quick info and news feed
