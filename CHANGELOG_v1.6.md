# Changelog v1.6 - EU Travel News Filtering

## New Features

### 🗞️ Intelligent News Filtering System
- **EU/Schengen News Filter**: Automatically filters news to show only EU/Schengen travel-related content
- **Country-Specific Filtering**: Detects news for all EU27 countries plus Iceland, Norway, Switzerland, and Liechtenstein
- **EU Policy Keywords**: Identifies EU-wide policy updates including ETIAS, EES, Schengen, and European Commission announcements
- **Country Aliases**: Supports country name variations (e.g., "Czechia"/"Czech Republic", "Netherlands"/"Holland")
- **Unicode Support**: Works with international characters and case variations

### 🎛️ Admin Controls
- **Settings Modal Integration**: News filter toggle in General settings section
- **Home Page Quick Toggle**: Admin-only toggle buttons on home page header
- **Environment Variable Support**: `NEWS_FILTER_REGION` (EU_ONLY | ALL)

### 📰 Enhanced News Sources
- **Per-Country GOV.UK Feeds**: Individual travel advice feeds for all EU/Schengen countries
- **EU Commission Feeds**: European Commission News and EU Home Affairs RSS feeds
- **Smart Feed Management**: Global feeds disabled by default, country-specific feeds enabled

### 🏷️ Visual Enhancements
- **News Item Badges**: Color-coded badges showing matched country or "EU-wide" label
- **Improved News Layout**: Enhanced styling with hover effects and better typography
- **Admin-Only Controls**: Clean toggle interface for news filter switching

## Technical Improvements

### 🔧 Backend Changes
- **New Service Module**: `app/services/news_fetcher.py` with filtering logic
- **Database Seeding**: Automatic seeding of per-country news sources
- **Configuration Integration**: News filter settings in config system
- **Route Updates**: Admin settings route supports news filter updates

### 🧪 Testing
- **Comprehensive Test Suite**: Unit tests for all filtering scenarios
- **Edge Case Coverage**: Unicode, case-insensitive, and mixed content testing
- **Integration Tests**: End-to-end filtering functionality validation

### 📚 Documentation
- **README Updates**: Complete news filtering system documentation
- **Configuration Guide**: Environment variables and admin settings
- **Developer Guide**: How to add/remove countries and keywords

## Configuration

### Environment Variables
```bash
# Filter to EU/Schengen only (default)
NEWS_FILTER_REGION=EU_ONLY

# Show all regions
NEWS_FILTER_REGION=ALL
```

### Admin Settings
1. **Settings Modal**: Profile → Settings → General → News Filter
2. **Home Page Toggle**: Quick toggle buttons (admin only)

## Database Changes
- **News Sources Table**: Enhanced with per-country GOV.UK feeds
- **No Schema Changes**: Existing news_cache table unchanged
- **Automatic Seeding**: New installations get all EU country feeds

## Breaking Changes
- None

## Migration Notes
- Existing installations will automatically get new news sources on next database initialization
- News filtering is enabled by default (EU_ONLY mode)
- No data migration required

## Performance
- **Efficient Filtering**: Case-insensitive string matching with optimized country lists
- **Caching**: News items cached with filtering applied
- **Minimal Overhead**: Filtering adds negligible processing time

## Security
- **Admin-Only Controls**: News filter settings restricted to admin users
- **Input Validation**: All filter inputs properly validated
- **No External Dependencies**: Uses only standard Python libraries

## Compatibility
- **Python 3.9+**: Tested with Python 3.9.6
- **Flask 2.0+**: Compatible with existing Flask setup
- **SQLite**: No database schema changes required

---

**Version**: 1.6  
**Release Date**: December 2024  
**Compatibility**: Backward compatible with v1.5.1
