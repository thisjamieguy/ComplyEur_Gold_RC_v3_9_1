#!/bin/bash
# Script to run calendar validation test with login bypass enabled

cd "$(dirname "$0")"

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

# Check if Flask app is running
echo "🔍 Checking if Flask app is running..."
if ! curl -s http://127.0.0.1:5001/healthz > /dev/null 2>&1; then
    echo "⚠️  Flask app is not running!"
    echo ""
    echo "Please start the Flask app in a separate terminal with:"
    echo "  EUTRACKER_BYPASS_LOGIN=1 python3 run_local.py"
    echo ""
    echo "Or run it in the background:"
    echo "  EUTRACKER_BYPASS_LOGIN=1 python3 run_local.py &"
    echo ""
    read -p "Press Enter to continue anyway (test will fail if app not running)..."
fi

# Run the test
echo "🧪 Running calendar validation test with login bypass..."
EUTRACKER_BYPASS_LOGIN=1 python3 -m pytest tests/qa_calendar_validation.py -v

