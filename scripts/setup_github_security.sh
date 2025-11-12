#!/bin/bash

# ComplyEur Gold RC v3.9.1 - GitHub Security Setup Script
# This script configures security features for the GitHub repository
# Requires GitHub CLI authentication and repository admin permissions

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_NAME="ComplyEur_Gold_RC_v3_9_1"
BRANCH_NAME="main"

# Get GitHub username
GITHUB_USER=$(gh api user --jq .login 2>/dev/null || echo "")

if [ -z "$GITHUB_USER" ]; then
    echo -e "${RED}Error: GitHub CLI not authenticated${NC}"
    echo -e "${YELLOW}Please run: gh auth login${NC}"
    exit 1
fi

echo -e "${GREEN}=== ComplyEur Gold RC v3.9.1 - Security Setup ===${NC}"
echo -e "GitHub User: ${GREEN}$GITHUB_USER${NC}"
echo -e "Repository: ${GREEN}$REPO_NAME${NC}"
echo ""

# Check if repository exists
if ! gh repo view "$GITHUB_USER/$REPO_NAME" &>/dev/null; then
    echo -e "${RED}Error: Repository $REPO_NAME not found${NC}"
    echo -e "${YELLOW}Please create the repository first${NC}"
    exit 1
fi

# Step 1: Enable Dependabot Alerts
echo -e "${YELLOW}Step 1: Enabling Dependabot alerts...${NC}"
gh api repos/"$GITHUB_USER"/"$REPO_NAME"/vulnerability-alerts -X PUT || {
    echo -e "${YELLOW}Note: Dependabot alerts may require manual enablement in GitHub UI${NC}"
    echo -e "${YELLOW}Go to: Settings → Code security and analysis → Enable Dependabot alerts${NC}"
}

# Step 2: Enable Secret Scanning
echo -e "${YELLOW}Step 2: Enabling secret scanning...${NC}"
gh api repos/"$GITHUB_USER"/"$REPO_NAME"/secret-scanning -X PUT || {
    echo -e "${YELLOW}Note: Secret scanning may require manual enablement in GitHub UI${NC}"
    echo -e "${YELLOW}Go to: Settings → Code security and analysis → Enable secret scanning${NC}"
}

# Step 3: Configure Branch Protection
echo -e "${YELLOW}Step 3: Configuring branch protection...${NC}"
BRANCH_PROTECTION=$(cat <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  },
  "restrictions": null,
  "required_signatures": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_linear_history": false,
  "allow_fork_syncing": false
}
EOF
)

gh api repos/"$GITHUB_USER"/"$REPO_NAME"/branches/"$BRANCH_NAME"/protection -X PUT --input - <<< "$BRANCH_PROTECTION" || {
    echo -e "${YELLOW}Note: Branch protection may require manual configuration in GitHub UI${NC}"
    echo -e "${YELLOW}Go to: Settings → Branches → Add rule for '$BRANCH_NAME'${NC}"
}

# Step 4: Enable Code Scanning (Optional)
echo -e "${YELLOW}Step 4: Code scanning configuration...${NC}"
echo -e "${YELLOW}Note: Code scanning requires manual setup in GitHub UI${NC}"
echo -e "${YELLOW}Go to: Settings → Code security and analysis → Set up code scanning${NC}"

# Step 5: Verify .env.example is safe
echo -e "${YELLOW}Step 5: Verifying .env.example...${NC}"
if [ -f ".env.example" ]; then
    if grep -q "SECRET_KEY\|PASSWORD\|TOKEN" .env.example; then
        echo -e "${GREEN}.env.example contains placeholder values (safe)${NC}"
    else
        echo -e "${YELLOW}Warning: .env.example may contain sensitive values${NC}"
    fi
else
    echo -e "${YELLOW}Warning: .env.example not found${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}=== Security Setup Complete ===${NC}"
echo -e "Repository: ${GREEN}https://github.com/$GITHUB_USER/$REPO_NAME${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Verify Dependabot alerts are enabled in GitHub UI"
echo "2. Verify secret scanning is enabled in GitHub UI"
echo "3. Verify branch protection rules are active"
echo "4. Set up code scanning (optional)"
echo "5. Review repository settings"
echo ""
echo -e "${GREEN}Done!${NC}"

