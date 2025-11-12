# Manual GitHub Repository Setup – ComplyEur Gold RC v3.9.1

**Version**: 3.9.1 (Gold Release Candidate)  
**Date**: 2025-11-12

This document provides manual instructions for setting up the GitHub repository if the automated script cannot be used.

---

## Prerequisites

1. **GitHub Account**: Active GitHub account
2. **Git Configured**: Git configured with your name and email
3. **SSH Keys**: SSH keys set up for GitHub (or use HTTPS with personal access token)
4. **Local Repository**: ComplyEur code committed and ready to push

---

## Step 1: Authenticate with GitHub CLI

If GitHub CLI is not authenticated, run:

```bash
gh auth login
```

Follow the prompts:
1. Choose **GitHub.com**
2. Choose **SSH** (recommended) or **HTTPS**
3. Authenticate via web browser
4. Verify authentication: `gh auth status`

---

## Step 2: Create GitHub Repository

### Option A: Using GitHub CLI

```bash
gh repo create ComplyEur_Gold_RC_v3_9_1 \
    --public \
    --description "ComplyEur Gold Release Candidate v3.9.1 – Verified Stable Core Build (Audit-Approved, Production-Ready)" \
    --homepage "https://complyeur.com" \
    --confirm
```

### Option B: Using GitHub Web UI

1. Navigate to [github.com/new](https://github.com/new)
2. **Repository name**: `ComplyEur_Gold_RC_v3_9_1`
3. **Description**: `ComplyEur Gold Release Candidate v3.9.1 – Verified Stable Core Build (Audit-Approved, Production-Ready)`
4. **Visibility**: Public
5. **Initialize repository**: 
   - ✅ Add a README file (optional)
   - ✅ Add .gitignore: Python
   - ✅ Choose a license: MIT
6. Click **"Create repository"**

---

## Step 3: Add Remote and Push Code

### From Local Repository

```bash
# Navigate to project directory
cd "/Users/jameswalsh/Desktop/Dev/Web Projects/ComplyEur/ComplyEur v1.0.0 Post MVP"

# Verify current branch
git branch --show-current  # Should be 'phase1_core_stable'

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add gold git@github.com:YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1.git

# Push to GitHub (main branch)
git push gold phase1_core_stable:main --force

# Set upstream branch
git branch --set-upstream-to=gold/main main
```

### If Using HTTPS

```bash
git remote add gold https://github.com/YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1.git
git push gold phase1_core_stable:main --force
```

---

## Step 4: Set Default Branch to Main

### Using GitHub CLI

```bash
gh repo edit YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1 --default-branch main
```

### Using GitHub Web UI

1. Go to repository settings
2. Navigate to **Branches**
3. Under **Default branch**, click **Switch to another branch**
4. Select **main**
5. Click **Update**
6. Confirm change

---

## Step 5: Create and Push Tag

```bash
# Create annotated tag
git tag -a gold-rc-v3.9.1 -m "ComplyEur Gold Release Candidate v3.9.1 – Stable Core Build"

# Push tag to GitHub
git push gold gold-rc-v3.9.1
```

---

## Step 6: Create GitHub Release

### Using GitHub CLI

```bash
# Create release with notes from CHANGELOG.md and PRE_RELEASE_AUDIT_SUMMARY.md
gh release create gold-rc-v3.9.1 \
    --title "ComplyEur Gold Release Candidate v3.9.1" \
    --notes-file <(cat CHANGELOG.md && echo -e "\n---\n" && cat PRE_RELEASE_AUDIT_SUMMARY.md) \
    --repo YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1
```

### Using GitHub Web UI

1. Go to repository → **Releases** → **Draft a new release**
2. **Tag**: Select `gold-rc-v3.9.1`
3. **Release title**: `ComplyEur Gold Release Candidate v3.9.1`
4. **Description**: Copy content from `CHANGELOG.md` and `PRE_RELEASE_AUDIT_SUMMARY.md`
5. Click **"Publish release"**

---

## Step 7: Configure Branch Protection Rules

### Using GitHub Web UI

1. Go to repository → **Settings** → **Branches**
2. Under **Branch protection rules**, click **Add rule**
3. **Branch name pattern**: `main`
4. Configure rules:
   - ✅ **Require a pull request before merging**
     - ✅ Require approvals: 1
     - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ **Require status checks to pass before merging**
     - ✅ Require branches to be up to date before merging
   - ✅ **Require signed commits**
   - ✅ **Require linear history**
   - ✅ **Include administrators**
   - ✅ **Do not allow bypassing the above settings**
5. Click **"Create"**

### Using GitHub API

```bash
# Requires GitHub token with repo admin permissions
curl -X PUT \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1/branches/main/protection \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": []
    },
    "enforce_admins": true,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true
    },
    "restrictions": null,
    "required_signatures": true,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'
```

---

## Step 8: Enable Security Features

### Dependabot Alerts

1. Go to repository → **Settings** → **Code security and analysis**
2. Under **Dependabot alerts**, click **Enable**
3. Configure alert settings:
   - ✅ Enable Dependabot alerts
   - ✅ Enable Dependabot security updates
   - ✅ Enable Dependabot version updates (optional)

### Secret Scanning

1. Go to repository → **Settings** → **Code security and analysis**
2. Under **Secret scanning**, click **Enable**
3. Configure scanning settings:
   - ✅ Enable secret scanning
   - ✅ Enable push protection (optional, but recommended)

### Code Scanning

1. Go to repository → **Settings** → **Code security and analysis**
2. Under **Code scanning**, click **Set up** or **Enable**
3. Choose a code scanning tool (e.g., CodeQL)
4. Configure scanning settings
5. Enable automatic scanning on push and pull requests

---

## Step 9: Verify Repository Setup

### Check Repository

1. Visit repository URL: `https://github.com/YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1`
2. Verify all files are present
3. Check README.md displays correctly
4. Verify LICENSE file is present
5. Check CHANGELOG.md and PRE_RELEASE_AUDIT_SUMMARY.md are present

### Check Release

1. Go to **Releases** page
2. Verify release `gold-rc-v3.9.1` exists
3. Check release notes are complete
4. Verify tag is linked correctly

### Check Branch Protection

1. Go to **Settings** → **Branches**
2. Verify branch protection rules are active
3. Test by attempting to push directly to main (should be blocked)

### Check Security Features

1. Go to **Settings** → **Code security and analysis**
2. Verify Dependabot alerts are enabled
3. Verify secret scanning is enabled
4. Verify code scanning is enabled (if configured)

---

## Step 10: Clone and Verify

### Clone Fresh Repository

```bash
# Clone to a new location
cd /tmp
git clone git@github.com:YOUR_USERNAME/ComplyEur_Gold_RC_v3_9_1.git
cd ComplyEur_Gold_RC_v3_9_1

# Verify branch
git branch --show-current  # Should be 'main'

# Verify tag
git tag -l  # Should include 'gold-rc-v3.9.1'

# Verify files
ls -la  # Should show all project files
```

### Run Tests

```bash
# Install dependencies
pip install -r requirements.txt
npm install

# Run tests
pytest
npx playwright test
```

---

## Troubleshooting

### Authentication Issues

**Issue**: GitHub CLI authentication fails

**Solution**:
1. Check internet connection
2. Try authenticating via web browser: `gh auth login --web`
3. Verify SSH keys are set up: `ssh -T git@github.com`
4. Use personal access token if SSH fails

### Repository Creation Issues

**Issue**: Repository already exists

**Solution**:
1. Delete existing repository (if safe to do so)
2. Or use a different repository name
3. Or push to existing repository

### Push Issues

**Issue**: Push fails with permission errors

**Solution**:
1. Verify SSH keys are added to GitHub account
2. Check repository permissions
3. Use personal access token if SSH fails
4. Verify remote URL is correct

### Tag Issues

**Issue**: Tag already exists

**Solution**:
1. Delete local tag: `git tag -d gold-rc-v3.9.1`
2. Delete remote tag: `git push gold :refs/tags/gold-rc-v3.9.1`
3. Recreate tag: `git tag -a gold-rc-v3.9.1 -m "Message"`
4. Push tag: `git push gold gold-rc-v3.9.1`

---

## Next Steps

After repository setup is complete:

1. **Enable Branch Protection**: Configure branch protection rules
2. **Enable Security Features**: Enable Dependabot, secret scanning, and code scanning
3. **Configure Render Deployment**: See `docs/deployment/render_setup.md`
4. **Set Up Monitoring**: Configure application monitoring
5. **Team Access**: Grant team members access to repository
6. **Documentation**: Update internal documentation with repository URL

---

## Success Criteria

✅ Repository created on GitHub  
✅ Code pushed to main branch  
✅ Tag created and pushed  
✅ Release created with notes  
✅ Branch protection rules enabled  
✅ Security features enabled  
✅ Repository verified and tested  

---

**Last Updated**: 2025-11-12  
**Version**: 3.9.1 (Gold Release Candidate)

