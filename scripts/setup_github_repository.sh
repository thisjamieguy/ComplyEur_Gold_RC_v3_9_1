#!/bin/bash

# ComplyEur Gold RC v3.9.1 - GitHub Repository Setup Script
# This script automates the creation and configuration of the GitHub repository
# for ComplyEur Gold Release Candidate v3.9.1

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="ComplyEur_Gold_RC_v3_9_1"
REPO_DESCRIPTION="ComplyEur Gold Release Candidate v3.9.1 – Verified Stable Core Build (Audit-Approved, Production-Ready)"
REPO_HOMEPAGE="https://complyeur.com"
TAG_NAME="gold-rc-v3.9.1"
BRANCH_NAME="main"
CURRENT_BRANCH="phase1_core_stable"

# Get GitHub username
GITHUB_USER=$(gh api user --jq .login 2>/dev/null || echo "")

if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}Error: GitHub CLI not authenticated${NC}"
    echo -e "${YELLOW}Please run: gh auth login${NC}"
    exit 1
fi

echo -e "${GREEN}=== ComplyEur Gold RC v3.9.1 - Repository Setup ===${NC}"
echo -e "GitHub User: ${GREEN}$GITHUB_USER${NC}"
echo -e "Repository: ${GREEN}$REPO_NAME${NC}"
echo ""

# Step 1: Verify we're on the correct branch
echo -e "${YELLOW}Step 1: Verifying branch...${NC}"
CURRENT_BRANCH_CHECK=$(git branch --show-current)
if [ "$CURRENT_BRANCH_CHECK" != "$CURRENT_BRANCH" ]; then
    echo -e "${YELLOW}Warning: Not on $CURRENT_BRANCH branch. Current branch: $CURRENT_BRANCH_CHECK${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Check if repository already exists
echo -e "${YELLOW}Step 2: Checking if repository exists...${NC}"
if gh repo view "$GITHUB_USER/$REPO_NAME" &>/dev/null; then
    echo -e "${YELLOW}Repository $REPO_NAME already exists${NC}"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing repository...${NC}"
        gh repo delete "$GITHUB_USER/$REPO_NAME" --yes
    else
        echo -e "${RED}Cancelled${NC}"
        exit 1
    fi
fi

# Step 3: Create GitHub repository
echo -e "${YELLOW}Step 3: Creating GitHub repository...${NC}"
gh repo create "$REPO_NAME" \
    --public \
    --description "$REPO_DESCRIPTION" \
    --homepage "$REPO_HOMEPAGE" \
    --confirm

echo -e "${GREEN}Repository created successfully${NC}"

# Step 4: Add remote
echo -e "${YELLOW}Step 4: Adding remote...${NC}"
if git remote get-url "gold" &>/dev/null; then
    echo -e "${YELLOW}Remote 'gold' already exists, updating...${NC}"
    git remote set-url "gold" "git@github.com:$GITHUB_USER/$REPO_NAME.git"
else
    git remote add "gold" "git@github.com:$GITHUB_USER/$REPO_NAME.git"
fi

# Step 5: Push to GitHub
echo -e "${YELLOW}Step 5: Pushing code to GitHub...${NC}"
git push gold "$CURRENT_BRANCH:$BRANCH_NAME" --force

# Step 6: Set default branch to main
echo -e "${YELLOW}Step 6: Setting default branch to main...${NC}"
gh repo edit "$GITHUB_USER/$REPO_NAME" --default-branch "$BRANCH_NAME"

# Step 7: Create and push tag
echo -e "${YELLOW}Step 7: Creating and pushing tag...${NC}"
if git tag -l | grep -q "^$TAG_NAME$"; then
    echo -e "${YELLOW}Tag $TAG_NAME already exists locally${NC}"
    read -p "Delete and recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "$TAG_NAME"
        git push gold ":refs/tags/$TAG_NAME" 2>/dev/null || true
    fi
fi

git tag -a "$TAG_NAME" -m "ComplyEur Gold Release Candidate v3.9.1 – Stable Core Build"
git push gold "$TAG_NAME"

# Step 8: Create GitHub release
echo -e "${YELLOW}Step 8: Creating GitHub release...${NC}"
RELEASE_NOTES=$(cat <<EOF
# ComplyEur Gold Release Candidate v3.9.1

**Release Date**: $(date +%Y-%m-%d)
**Status**: Production-Ready

## Overview

ComplyEur Gold Release Candidate v3.9.1 is a verified stable core build that has undergone comprehensive testing, security auditing, and documentation review. This release is ready for production deployment.

## Key Features

- ✅ Stable 90/180-day rule calculations with rolling window support
- ✅ Employee management with full CRUD operations
- ✅ Trip tracking with entry/exit date validation
- ✅ Interactive calendar with drag-and-drop trip management
- ✅ Color-coded risk assessment (green/amber/red)
- ✅ GDPR-compliant data export and DSAR tools
- ✅ Secure authentication with Argon2 password hashing
- ✅ Comprehensive audit logging
- ✅ Production-ready security measures

## Documentation

- [README.md](README.md) - Overview and quick start
- [INSTALL.md](INSTALL.md) - Installation instructions
- [TESTING.md](TESTING.md) - Testing documentation
- [PRE_RELEASE_AUDIT_SUMMARY.md](PRE_RELEASE_AUDIT_SUMMARY.md) - Complete audit report
- [CHANGELOG.md](CHANGELOG.md) - Detailed changelog
- [docs/deployment/render_setup.md](docs/deployment/render_setup.md) - Render deployment guide

## Security

- Argon2 password hashing (industry-standard)
- Session security with HTTPOnly cookies
- Rate limiting on authentication endpoints
- Input validation and sanitization
- SQL injection prevention
- Security headers (XSS protection, frame options)

## Deployment

See [docs/deployment/render_setup.md](docs/deployment/render_setup.md) for Render deployment instructions.

## Support

For issues or questions, please refer to the documentation or open an issue on GitHub.

---

**Version**: 3.9.1 (Gold Release Candidate)  
**Date**: 2025-11-12  
**Status**: Production-Ready
EOF
)

# Create release with notes
gh release create "$TAG_NAME" \
    --title "ComplyEur Gold Release Candidate v3.9.1" \
    --notes "$RELEASE_NOTES" \
    --repo "$GITHUB_USER/$REPO_NAME"

# Step 9: Enable branch protection (requires manual setup or API token with repo admin)
echo -e "${YELLOW}Step 9: Branch protection configuration...${NC}"
echo -e "${YELLOW}Note: Branch protection rules require manual configuration in GitHub UI${NC}"
echo -e "${YELLOW}Or use GitHub API with a token that has admin permissions${NC}"

# Step 10: Enable security features
echo -e "${YELLOW}Step 10: Security features configuration...${NC}"
echo -e "${YELLOW}Note: Dependabot and secret scanning require manual enablement in GitHub UI${NC}"
echo -e "${YELLOW}Settings → Code security and analysis → Enable features${NC}"

# Step 11: Verify deployment
echo -e "${YELLOW}Step 11: Verifying repository...${NC}"
echo -e "${GREEN}Repository URL: https://github.com/$GITHUB_USER/$REPO_NAME${NC}"
echo -e "${GREEN}Release URL: https://github.com/$GITHUB_USER/$REPO_NAME/releases/tag/$TAG_NAME${NC}"

# Summary
echo ""
echo -e "${GREEN}=== Repository Setup Complete ===${NC}"
echo -e "Repository: ${GREEN}https://github.com/$GITHUB_USER/$REPO_NAME${NC}"
echo -e "Release: ${GREEN}https://github.com/$GITHUB_USER/$REPO_NAME/releases/tag/$TAG_NAME${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Enable branch protection rules in GitHub UI"
echo "2. Enable Dependabot alerts in Settings → Code security and analysis"
echo "3. Enable secret scanning in Settings → Code security and analysis"
echo "4. Enable code scanning (if applicable)"
echo "5. Review and configure repository settings"
echo "6. Set up Render deployment (see docs/deployment/render_setup.md)"
echo ""
echo -e "${GREEN}Done!${NC}"

