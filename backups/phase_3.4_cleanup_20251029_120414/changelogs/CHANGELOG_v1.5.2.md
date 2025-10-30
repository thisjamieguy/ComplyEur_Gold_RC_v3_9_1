# Changelog - Version 1.5.2

## New Features

### 🏠 Home Screen with Quick Info & EU Travel News

Added a new home screen that displays immediately after login, providing:
- **Quick Info Cards**: Three dashboard cards showing:
  - Active Employees count
  - Trips logged this month
  - Employees at risk of 90-day limit
  
- **EU Travel News Feed**: Automatically fetches and displays latest news from:
  - GOV.UK Foreign Travel Advice
  - EU Home Affairs News
  - SchengenVisaInfo News

### Technical Details

#### New Database Tables
- `news_sources`: Stores RSS feed configurations
- `news_cache`: Caches fetched news articles

#### New Files
- `app/templates/home.html`: Home page template
- `app/services/news_fetcher.py`: News fetching service
- `app/services/__init__.py`: Services package initializer
- `docs/HOME_PAGE_README.md`: Documentation

#### Modified Files
- `app/routes.py`: Added `/home` route and updated login redirect
- `app/models.py`: Added news tables to database schema
- `app/__init__.py`: Added `news-fetch` CLI command
- `app/templates/base.html`: Added Home link to sidebar navigation
- `requirements.txt`: Added `feedparser==6.0.10`

### Configuration

- **NEWS_FETCH_ENABLED**: Environment variable to disable/enable news fetching (default: `true`)
- News cache expires after 6 hours
- Old news items automatically cleaned up after 7 days

### CLI Commands

```bash
flask news-fetch
```

Manually refreshes news from all configured RSS feeds.

### GDPR Compliance

- Only public news headlines and links are cached
- Full attribution provided for GOV.UK content (OGL v3.0)
- No personal data is collected or stored
- Content is cached locally in SQLite

## Breaking Changes

None

## Migration Notes

1. Run database migrations to create new tables (automatic on first start)
2. Install new dependencies: `pip install feedparser`
3. News will automatically start fetching on first home page load
4. Can optionally set `NEWS_FETCH_ENABLED=false` in environment to disable fetching

## Testing

### Acceptance Checklist
- ✅ Login redirects to /home
- ✅ Three info cards display correctly
- ✅ News feed loads (or shows empty state)
- ✅ News headlines link to external sources
- ✅ Attribution footer displays correctly
- ✅ Page renders without errors if news fetch disabled

### Manual Testing Steps
1. Login to the application
2. Verify redirect to /home page
3. Check that three info cards display stats
4. Verify news feed section appears
5. Click on a news headline to verify external link
6. Check attribution footer for OGL v3.0 notice

## Known Issues

- First page load may be slower while fetching initial news
- RSS feeds may be unavailable or slow in some network environments
- Cache is currently in-memory only (persists across requests per app instance)

## Deployment Notes

1. Install new dependency: `feedparser==6.0.10`
2. Database tables will auto-create on first run
3. Optionally set `NEWS_FETCH_ENABLED=false` in production if desired
4. News fetching uses 6-hour cache by default (adjustable in code)

## Version Tag

Tag this release as: `v1.5.2`

```bash
git tag v1.5.2
git push origin v1.5.2
```

