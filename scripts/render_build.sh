#!/bin/bash
# Render build script - handles optional dependencies gracefully
# This script installs requirements, allowing problematic packages to fail

echo "🔨 ComplyEur Render Build Script"
echo "================================="
echo ""

# Install packages in groups, allowing failures for optional ones
echo "📦 Installing core Python dependencies..."

# Core Flask and web framework packages (essential)
set +e
pip install Flask==3.0.3 Flask-WTF==1.2.1 Flask-Talisman==1.1.0 Flask-Limiter==3.7.0 Flask-Caching==2.3.0 Flask-Compress==1.14 Flask-SQLAlchemy==3.1.1 Werkzeug==3.0.3
CORE_EXIT=$?
set -e
if [ $CORE_EXIT -ne 0 ]; then
    echo "❌ Core dependencies failed to install - aborting"
    exit 1
fi

# Database and ORM
set +e
pip install SQLAlchemy==2.0.35 python-dotenv==1.0.1
set -e

# Security and crypto (cryptography may have wheels, but allow failure)
set +e
pip install argon2-cffi==23.1.0 cryptography==43.0.3 bleach==6.1.0 limits==3.13.0
set -e

# Utilities
set +e
pip install APScheduler==3.10.4 pyotp==2.9.0 qrcode==7.4.2 Pillow==10.4.0 zxcvbn-python==4.4.24
set -e

# Data processing (pandas/matplotlib may be heavy, but try)
set +e
pip install pandas==2.2.0 matplotlib==3.8.4 openpyxl==3.1.5
set -e

# File handling
set +e
pip install reportlab==4.2.0 feedparser==6.0.10 requests==2.31.0 diff-match-patch==20230430
set -e

# System utilities (psutil may require compilation)
set +e
pip install psutil==5.9.8
set -e

# Testing (optional for production, but include)
set +e
pip install pytest==8.3.3 pytest-flask==1.3.0
set -e

# Server
set +e
pip install gunicorn==21.2.0
set -e

# Try python-magic separately (optional - requires system libmagic)
echo ""
echo "📦 Attempting to install python-magic (optional)..."
set +e
pip install python-magic==0.4.27 2>&1 | grep -v "ninja\|metadata-generation" || true
if [ $? -ne 0 ]; then
    echo "⚠️  python-magic installation skipped (requires system libmagic)"
    echo "   Application will use fallback MIME type detection"
fi
set -e

# Try playwright separately (optional - very large, may fail)
echo ""
echo "📦 Attempting to install playwright (optional)..."
set +e
pip install playwright==1.55.0 2>&1 | grep -v "ninja\|metadata-generation" || true
if [ $? -ne 0 ]; then
    echo "⚠️  playwright installation skipped (large dependency, not required for production)"
fi
set -e

# Run asset build script
echo ""
echo "📦 Building assets..."
set -e  # Enable exit on error for asset build
./scripts/build_assets.sh

echo ""
echo "✅ Build complete!"

