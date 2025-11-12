#!/usr/bin/env python3
"""Quick test to verify login bypass is working"""

import os
import sys
import requests

# Set bypass
os.environ['EUTRACKER_BYPASS_LOGIN'] = '1'

# Test the Flask app
base_url = "http://127.0.0.1:5001"

print("Testing login bypass...")
print(f"EUTRACKER_BYPASS_LOGIN={os.getenv('EUTRACKER_BYPASS_LOGIN')}")

try:
    # Test health endpoint (should work)
    response = requests.get(f"{base_url}/healthz", timeout=2)
    print(f"✓ Health check: {response.status_code}")
    
    # Test dashboard (should bypass login)
    response = requests.get(f"{base_url}/dashboard", allow_redirects=False, timeout=2)
    print(f"✓ Dashboard response: {response.status_code}")
    if response.status_code == 302:
        print(f"  Redirect location: {response.headers.get('Location', 'N/A')}")
        if '/login' in response.headers.get('Location', ''):
            print("  ❌ Still redirecting to login - bypass not working!")
        else:
            print("  ✓ Redirecting somewhere else (might be OK)")
    elif response.status_code == 200:
        print("  ✓ Direct access to dashboard - bypass working!")
    else:
        print(f"  ⚠️  Unexpected status: {response.status_code}")
        
    # Test login page (should redirect to dashboard)
    response = requests.get(f"{base_url}/login", allow_redirects=False, timeout=2)
    print(f"✓ Login page response: {response.status_code}")
    if response.status_code == 302:
        location = response.headers.get('Location', '')
        print(f"  Redirect location: {location}")
        if '/dashboard' in location:
            print("  ✓ Redirecting to dashboard - bypass working!")
        else:
            print("  ⚠️  Redirecting elsewhere")
    
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to Flask app. Is it running?")
    print("   Start it with: EUTRACKER_BYPASS_LOGIN=1 python3 run_local.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

