#!/usr/bin/env python3
"""
Quick test script to verify the Help system is working correctly.
Run this to check if the help route and content are properly configured.
"""

import json
import os

def test_help_content():
    """Test that help_content.json exists and is valid."""
    print("🔍 Testing help_content.json...")
    
    if not os.path.exists('help_content.json'):
        print("❌ ERROR: help_content.json not found!")
        return False
    
    try:
        with open('help_content.json', 'r') as f:
            data = json.load(f)
        
        # Check required keys
        required_keys = ['page_title', 'page_subtitle', 'sections', 'tutorial_steps', 'quick_tips']
        for key in required_keys:
            if key not in data:
                print(f"❌ ERROR: Missing required key '{key}'")
                return False
        
        print(f"✅ JSON is valid")
        print(f"   - Title: {data['page_title']}")
        print(f"   - Sections: {len(data['sections'])}")
        print(f"   - Tutorial Steps: {len(data['tutorial_steps'])}")
        print(f"   - Quick Tips: {len(data['quick_tips'])}")
        
        # Verify all sections have required fields
        for i, section in enumerate(data['sections']):
            if not all(k in section for k in ['id', 'title', 'content']):
                print(f"❌ ERROR: Section {i} missing required fields")
                return False
        
        print("✅ All sections are properly formatted")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Invalid JSON - {e}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_static_files():
    """Test that Intro.js files exist."""
    print("\n🔍 Testing static files...")
    
    files_to_check = [
        ('static/js/intro.min.js', 'Intro.js JavaScript'),
        ('static/css/intro.min.css', 'Intro.js CSS'),
    ]
    
    all_exist = True
    for filepath, description in files_to_check:
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            print(f"✅ {description}: {filepath} ({size:,} bytes)")
        else:
            print(f"❌ Missing: {description} at {filepath}")
            all_exist = False
    
    return all_exist

def test_templates():
    """Test that help template exists."""
    print("\n🔍 Testing templates...")
    
    if os.path.exists('templates/help.html'):
        with open('templates/help.html', 'r') as f:
            content = f.read()
            
        checks = [
            ('intro.min.js', 'Intro.js script included'),
            ('intro.min.css', 'Intro.js CSS included'),
            ('help_content', 'Help content variable used'),
            ('toggleSection', 'Section toggle function exists'),
            ('startTutorial', 'Tutorial function exists'),
        ]
        
        all_found = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        return all_found
    else:
        print("❌ templates/help.html not found")
        return False

def test_navigation():
    """Test that base template has Help navigation."""
    print("\n🔍 Testing navigation updates...")
    
    if os.path.exists('templates/base.html'):
        with open('templates/base.html', 'r') as f:
            content = f.read()
        
        checks = [
            ("url_for('help_page')", 'Help page route referenced'),
            ('Help & Tutorial', 'Help navigation text'),
            ('Support', 'Support section header'),
        ]
        
        all_found = True
        for check_str, description in checks:
            if check_str in content:
                print(f"✅ {description}")
            else:
                print(f"❌ Missing: {description}")
                all_found = False
        
        return all_found
    else:
        print("❌ templates/base.html not found")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("🧪 EU Trip Tracker - Help System Tests")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(('Help Content', test_help_content()))
    results.append(('Static Files', test_static_files()))
    results.append(('Templates', test_templates()))
    results.append(('Navigation', test_navigation()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Help system is ready.")
        print("\n📝 Next steps:")
        print("   1. Start the Flask app: python3 app.py")
        print("   2. Login and navigate to /help")
        print("   3. Test the interactive tutorial")
        print("   4. Update content in help_content.json as needed")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == '__main__':
    exit(main())

