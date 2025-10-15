╔═══════════════════════════════════════════════════════════════╗
║              EU TRIP TRACKER - WINDOWS USERS                  ║
║                      Version 1.2.0                            ║
╚═══════════════════════════════════════════════════════════════╝

═══════════════════════════════════════════════════════════════
🪟 FOR WINDOWS USERS - QUICK START
═══════════════════════════════════════════════════════════════

STEP 1: INSTALL PYTHON (IF NOT ALREADY INSTALLED)
──────────────────────────────────────────────────────────────

1. Go to: https://www.python.org/downloads/
2. Download Python 3.9 or newer
3. Run the installer
4. ✓ CHECK THE BOX: "Add Python to PATH"
5. Click "Install Now"
6. Wait for installation to complete

═══════════════════════════════════════════════════════════════

STEP 2: RUN THE APPLICATION
──────────────────────────────────────────────────────────────

🎯 SUPER SIMPLE METHOD:

  1. Double-click "START_APP.bat"
  
  2. A black window will appear (this is normal!)
  
  3. Your web browser will open automatically
  
  4. You'll see the login page at: http://127.0.0.1:5003
  
  5. Login with password: admin123
  
  6. DONE! 🎉

═══════════════════════════════════════════════════════════════

📝 FIRST TIME ONLY:
──────────────────────────────────────────────────────────────

The FIRST time you run the app:
• It will install dependencies (2-3 minutes)
• You'll see: "Installing dependencies..."
• This only happens once!
• After that, it starts instantly

═══════════════════════════════════════════════════════════════

⚠️ IMPORTANT NOTES:
──────────────────────────────────────────────────────────────

1. DON'T CLOSE THE BLACK WINDOW
   → That's the server running
   → Keep it open while using the app
   
2. DEFAULT PASSWORD: admin123
   → Change it immediately after first login!
   → Go to: Settings → Change Password
   
3. TO STOP THE APP:
   → Close the black window
   → Or press Ctrl+C in the window

4. BROWSER DOESN'T OPEN?
   → Open any browser manually
   → Go to: http://127.0.0.1:5003

═══════════════════════════════════════════════════════════════

🔧 TROUBLESHOOTING:
──────────────────────────────────────────────────────────────

PROBLEM: "Python is not installed" error
SOLUTION: Install Python from https://www.python.org/downloads/
          Make sure to check "Add Python to PATH"

PROBLEM: "pip is not recognized" error
SOLUTION: Reinstall Python and check "Add Python to PATH"

PROBLEM: Browser doesn't open automatically
SOLUTION: Open any browser and type: http://127.0.0.1:5003

PROBLEM: "Port already in use" error
SOLUTION: Close other programs using port 5003
          Or restart your computer

PROBLEM: Dependencies won't install
SOLUTION: Open Command Prompt as Administrator:
          cd [path-to-this-folder]
          python -m pip install -r requirements.txt

═══════════════════════════════════════════════════════════════

📂 WHAT'S IN THIS FOLDER:
──────────────────────────────────────────────────────────────

START_APP.bat         ← DOUBLE-CLICK THIS TO RUN!
launcher.py           ← Python launcher script
app.py                ← Main Flask application
requirements.txt      ← Python dependencies
env_template.txt      ← Configuration template

templates/            ← HTML templates
static/               ← CSS, JavaScript, images
data/                 ← JSON data files
docs/                 ← Documentation
modules/              ← Service modules

═══════════════════════════════════════════════════════════════

✨ USAGE TIPS:
──────────────────────────────────────────────────────────────

1. CREATE A SHORTCUT
   → Right-click START_APP.bat
   → "Create shortcut"
   → Move shortcut to Desktop
   → Now you can start it from Desktop!

2. PIN TO TASKBAR (OPTIONAL)
   → Create a shortcut as above
   → Right-click shortcut → "Pin to taskbar"

3. BACKUP YOUR DATA
   → Your data is in: eu_tracker.db
   → Copy this file to backup
   → Restore by replacing it

═══════════════════════════════════════════════════════════════

🔐 SECURITY:
──────────────────────────────────────────────────────────────

✓ All data stored locally (no cloud)
✓ Passwords encrypted
✓ No internet connection required
✓ Session timeout after 30 minutes
✓ GDPR compliant

═══════════════════════════════════════════════════════════════

📚 MORE HELP:
──────────────────────────────────────────────────────────────

See the "docs" folder for:
• Detailed setup guide
• Import/Export instructions
• GDPR compliance info
• User manual

═══════════════════════════════════════════════════════════════

💡 QUICK DEMO:
──────────────────────────────────────────────────────────────

1. Double-click START_APP.bat
2. Login with: admin123
3. Click "Add Employee"
4. Add a test employee (e.g., "John Smith")
5. Click on the employee name
6. Click "Add Trip"
7. Enter some test dates
8. See the dashboard update!

═══════════════════════════════════════════════════════════════

✅ SYSTEM REQUIREMENTS:
──────────────────────────────────────────────────────────────

Operating System: Windows 10 or newer
Python: 3.9 or newer
RAM: 512 MB minimum
Disk Space: 200 MB
Internet: Only for initial Python install

═══════════════════════════════════════════════════════════════

🎯 KEY FEATURES:
──────────────────────────────────────────────────────────────

✓ Track unlimited employees
✓ Automatic 90/180-day calculations
✓ Color-coded risk dashboard
✓ Excel import/export
✓ PDF/CSV reports
✓ EU entry requirements
✓ Trip validator
✓ Calendar views

═══════════════════════════════════════════════════════════════

📞 NEED HELP?
──────────────────────────────────────────────────────────────

1. Check the README.txt file
2. Look in the docs/ folder
3. See QUICK_START.txt
4. Contact your IT administrator

═══════════════════════════════════════════════════════════════

REMEMBER: Default password is admin123
          Change it immediately after first login!

═══════════════════════════════════════════════════════════════


