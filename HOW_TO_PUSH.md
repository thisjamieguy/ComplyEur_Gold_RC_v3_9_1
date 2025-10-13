# 🚀 How to Push Your Code to GitHub

## For Complete Beginners - Super Simple Guide

### One-Command Solution

I've created an automated script that does everything for you!

#### **Option 1: Run the Script (Easiest)**

Just copy and paste this into your Terminal:

```bash
cd "/Users/jameswalsh/Desktop/iOS Dev/Web Projects/eu-trip-tracker"
./push_to_github.sh
```

That's it! The script will:
- ✅ Create your `.env` file with secure keys
- ✅ Show you what changes will be pushed
- ✅ Ask for your confirmation at each step
- ✅ Commit and push to GitHub
- ✅ Give you next steps

---

### What the Script Does (Step by Step)

The script is **interactive** and **safe**. It will:

1. **Create .env file**
   - Automatically generates a secure SECRET_KEY
   - You can review and edit it later

2. **Show you the changes**
   - Lists all files that will be pushed
   - Asks if you want to see details

3. **Commit to Git**
   - Asks for confirmation before committing
   - Uses a professional commit message

4. **Push to GitHub**
   - Final confirmation before pushing
   - Pushes to your GitHub repository

---

### Step-by-Step Instructions

#### **Step 1: Open Terminal**
- Press `⌘ + Space` (Command + Space)
- Type "Terminal"
- Press Enter

#### **Step 2: Navigate to Your Project**
Copy and paste this:
```bash
cd "/Users/jameswalsh/Desktop/iOS Dev/Web Projects/eu-trip-tracker"
```

#### **Step 3: Run the Script**
Copy and paste this:
```bash
./push_to_github.sh
```

#### **Step 4: Follow the Prompts**
The script will ask you questions:
- **"Do you want to see detailed changes?"** 
  - Type `n` and press Enter (unless you're curious)
  
- **"Ready to commit these changes?"**
  - Type `y` and press Enter
  
- **"Push to GitHub now?"**
  - Type `y` and press Enter

#### **Step 5: Done! 🎉**

---

### After Pushing to GitHub

#### **Important Security Steps:**

1. **Revoke the Old API Key** (CRITICAL!)
   - Go to: https://www.pexels.com/api/
   - Sign in and revoke the exposed key
   - Generate a new one if you need cityscape images

2. **Update Your .env File**
   ```bash
   # Open the .env file in a text editor
   open .env
   ```
   
   Change these values:
   - `ADMIN_PASSWORD=admin123` → Use a strong password
   - `PEXELS_API_KEY=your-pexels-api-key-here` → Add your new key

3. **Install Updated Packages**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test the App**
   ```bash
   python app.py
   ```
   
   Then visit: http://127.0.0.1:5003

---

### Troubleshooting

#### **"Permission denied" Error**
If you see this error, run:
```bash
chmod +x push_to_github.sh
./push_to_github.sh
```

#### **"No remote repository configured" Error**
You need to connect your local repository to GitHub:

1. Go to GitHub.com and create a new repository
2. Copy the repository URL
3. Run this (replace with your URL):
   ```bash
   git remote add origin https://github.com/yourusername/eu-trip-tracker.git
   ./push_to_github.sh
   ```

#### **"git: command not found"**
You need to install Git:
```bash
xcode-select --install
```

---

### Manual Method (If Script Doesn't Work)

If you prefer to do it manually, here are the commands:

```bash
# 1. Create .env file
cp env_template.txt .env

# 2. Generate secure key and add to .env
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and paste into .env as SECRET_KEY value

# 3. Stage changes
git add .gitignore README.md env_template.txt generate_cityscapes.py requirements.txt

# 4. Commit
git commit -m "Security & dependency updates - Production ready"

# 5. Push
git push origin main
```

---

### What Gets Pushed to GitHub?

**✅ These files ARE pushed:**
- Code files (app.py, config.py, etc.)
- Templates and static files
- Documentation
- requirements.txt
- .gitignore

**❌ These files are NOT pushed (safe):**
- .env (your secrets)
- eu_tracker.db (your database)
- cookies.txt
- __pycache__/ folders
- .DS_Store files

---

### Questions?

- **Q: Is my .env file safe?**
  - A: Yes! It's in .gitignore and will never be pushed to GitHub

- **Q: What if I made a mistake?**
  - A: You can undo the last commit with: `git reset HEAD~1`

- **Q: Can I run the script multiple times?**
  - A: Yes, but it will ask before overwriting your .env file

---

## 🎉 You're All Set!

Once you run the script and push to GitHub, your code is safely backed up and ready to share!

**Need help?** Check the documentation in the `/docs` folder.

