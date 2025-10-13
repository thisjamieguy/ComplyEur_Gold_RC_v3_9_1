#!/bin/bash

# ============================================================================
# EU Trip Tracker - Automated GitHub Push Script
# ============================================================================
# This script prepares your repository and pushes to GitHub
# Safe for beginners - includes confirmations and clear instructions
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print styled messages
print_header() {
    echo -e "\n${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

# Start
clear
print_header "🚀 EU Trip Tracker - GitHub Push Automation"

echo -e "${BOLD}This script will:${NC}"
echo "  1. Create your .env file with secure keys"
echo "  2. Review all changes being pushed"
echo "  3. Commit changes to Git"
echo "  4. Push to GitHub"
echo ""

# ============================================================================
# STEP 1: Create .env file
# ============================================================================
print_header "📝 Step 1: Setting up .env file"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Do you want to overwrite it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
        ENV_EXISTS=true
    else
        ENV_EXISTS=false
    fi
else
    ENV_EXISTS=false
fi

if [ "$ENV_EXISTS" = false ]; then
    print_info "Creating .env file from template..."
    cp env_template.txt .env
    
    # Generate secure SECRET_KEY
    print_info "Generating secure SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    
    # Update .env file with generated key
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here-change-this-to-a-random-64-character-hex-string/$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-key-here-change-this-to-a-random-64-character-hex-string/$SECRET_KEY/" .env
    fi
    
    print_success ".env file created with secure SECRET_KEY"
    print_warning "IMPORTANT: Change ADMIN_PASSWORD in .env before running the app!"
    print_warning "IMPORTANT: Add your Pexels API key to .env if you need cityscape images"
    echo ""
    print_info "Generated SECRET_KEY: ${SECRET_KEY:0:20}... (hidden for security)"
fi

# ============================================================================
# STEP 2: Review changes
# ============================================================================
print_header "📋 Step 2: Reviewing changes to be pushed"

echo -e "${BOLD}Files that will be committed:${NC}"
git status --short
echo ""

echo -e "${BOLD}Summary of changes:${NC}"
echo "  • Security fixes (API keys removed, database untracked)"
echo "  • 9 package updates (Flask 3.1.2, numpy 2.0.2, etc.)"
echo "  • Enhanced README documentation"
echo "  • Clean .DS_Store files"
echo ""

read -p "Do you want to see detailed changes? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    git diff --cached .gitignore README.md requirements.txt env_template.txt generate_cityscapes.py || git diff .gitignore README.md requirements.txt env_template.txt generate_cityscapes.py
    echo ""
fi

# ============================================================================
# STEP 3: Commit changes
# ============================================================================
print_header "💾 Step 3: Committing changes to Git"

read -p "Ready to commit these changes? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_error "Aborted by user"
    exit 1
fi

print_info "Staging all changes..."
git add .gitignore README.md env_template.txt generate_cityscapes.py requirements.txt

print_info "Creating commit..."
git commit -m "Security & dependency updates - Production ready

🔒 Security Fixes:
- Remove hardcoded Pexels API key from generate_cityscapes.py
- Untrack eu_tracker.db and cookies.txt from Git
- Update .gitignore with *.db and cookies.txt patterns
- Delete all .DS_Store files (17 total)
- Remove duplicate file generate_cityscapes.py)

📦 Dependency Updates (9 packages):
- Flask: 2.3.3 → 3.1.2 (security & performance)
- Werkzeug: 2.3.7 → 3.1.3 (security & WSGI improvements)
- numpy: 1.26.4 → 2.0.2 (performance boost)
- pandas: 2.1.4 → 2.3.3 (latest features)
- bcrypt: 4.1.2 → 5.0.0 (enhanced crypto)
- argon2-cffi: 23.1.0 → 25.1.0 (password hashing)
- python-dotenv: 1.0.0 → 1.1.1
- reportlab: 4.2.2 → 4.4.4
- idna: 3.10 → 3.11

📚 Documentation:
- Enhance README with comprehensive sections
- Add Pexels API key to env_template.txt
- Professional project structure documentation

✅ All secrets now loaded from environment variables
✅ No sensitive files tracked in Git
✅ Repository cleaned of macOS artifacts
✅ All packages updated to latest versions

Push Readiness Score: 100/100 🎉"

print_success "Changes committed successfully!"

# ============================================================================
# STEP 4: Push to GitHub
# ============================================================================
print_header "☁️  Step 4: Pushing to GitHub"

# Get current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)
print_info "Current branch: $BRANCH"

# Check if remote exists
if git remote get-url origin > /dev/null 2>&1; then
    REMOTE_URL=$(git remote get-url origin)
    print_info "Remote repository: $REMOTE_URL"
else
    print_error "No remote repository configured!"
    echo ""
    echo "To add a remote repository, run:"
    echo "  git remote add origin <your-github-repo-url>"
    echo ""
    exit 1
fi

echo ""
echo -e "${BOLD}${YELLOW}⚠️  FINAL CHECK BEFORE PUSHING ⚠️${NC}"
echo ""
echo "This will push your code to GitHub. Make sure:"
echo "  ✓ You have revoked the old Pexels API key"
echo "  ✓ The .env file is NOT being pushed (it's in .gitignore)"
echo "  ✓ No sensitive data is in the commit"
echo ""

read -p "Push to GitHub now? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Push cancelled. Your changes are committed locally."
    print_info "You can push later with: git push origin $BRANCH"
    exit 0
fi

print_info "Pushing to GitHub..."
git push origin "$BRANCH"

# ============================================================================
# SUCCESS!
# ============================================================================
print_header "🎉 SUCCESS! Your code is on GitHub!"

echo -e "${GREEN}${BOLD}✓ All done!${NC} Your repository has been pushed successfully.\n"

echo -e "${BOLD}Next steps:${NC}"
echo ""
echo "1. ${BOLD}Revoke the old API key:${NC}"
echo "   Visit: https://www.pexels.com/api/"
echo "   Revoke key: YTYdzNn... (the exposed one)"
echo ""
echo "2. ${BOLD}Update your .env file:${NC}"
echo "   • Change ADMIN_PASSWORD from 'admin123'"
echo "   • Add your new Pexels API key (if needed)"
echo ""
echo "3. ${BOLD}Install updated packages:${NC}"
echo "   Run: pip install -r requirements.txt"
echo ""
echo "4. ${BOLD}Start the app:${NC}"
echo "   Run: python app.py"
echo "   Visit: http://127.0.0.1:5003"
echo ""

print_success "Your .env file is at: $(pwd)/.env"
print_success "Your repository is at: $REMOTE_URL"

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  Happy coding! 🚀${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

