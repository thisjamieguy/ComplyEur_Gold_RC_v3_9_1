#!/bin/bash
# Script to start Flask app with login bypass enabled for testing

cd "$(dirname "$0")"

# Check if port 5001 is already in use
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  Port 5001 is already in use!"
    echo ""
    PID=$(lsof -ti:5001)
    echo "Killing existing process (PID: $PID)..."
    kill $PID 2>/dev/null
    sleep 2
    
    # Check if it's still running
    if lsof -ti:5001 > /dev/null 2>&1; then
        echo "⚠️  Process still running, trying force kill..."
        kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    if lsof -ti:5001 > /dev/null 2>&1; then
        echo "❌ Could not free port 5001. Please manually stop the process."
        echo "   Run: lsof -ti:5001 | xargs kill"
        exit 1
    fi
    
    echo "✅ Port 5001 is now free"
    echo ""
fi

# Activate virtual environment (try .venv first, then venv)
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ No virtual environment found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🚀 Starting Flask app with login bypass enabled..."
echo "📍 App will be available at: http://127.0.0.1:5001"
echo "🔓 Login screen is DISABLED for testing"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

EUTRACKER_BYPASS_LOGIN=1 python3 run_local.py

