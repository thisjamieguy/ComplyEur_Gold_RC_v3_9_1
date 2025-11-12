# ComplyEur Workflow – Quick Start Guide

## 🚀 Quick Setup

### 1. Verify Installation

```bash
./scripts/verify_workflow_setup.sh
```

### 2. Create Develop Branch (if needed)

```bash
git checkout main
git checkout -b develop
git push origin develop
```

### 3. Test Version Bump (Dry Run)

```bash
# Check current version
head -n 1 VERSION

# Test version parsing (should output: 3.9.1)
head -n 1 VERSION | sed -E 's/^([0-9]+\.[0-9]+\.[0-9]+).*/\1/'
```

---

## 📝 Common Workflows

### Start New Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/my_feature
# ... work ...
git commit -m "feat: add new feature"
git push origin feature/my_feature
# Create PR on GitHub: feature/my_feature → develop
```

### Bump Version for Release

```bash
# On release branch
./scripts/bump_version.sh minor  # or patch, or major
./scripts/update_changelog.sh
git push origin HEAD --tags
```

### Create Release

```bash
git checkout main
git merge release/3.10.0
git push origin main
# GitHub Actions automatically creates release
```

---

## 🔍 Verification Commands

```bash
# Check version
cat VERSION

# Check latest tag
git describe --tags --abbrev=0

# Check commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Verify scripts
bash -n scripts/bump_version.sh
bash -n scripts/update_changelog.sh
```

---

## 📚 Full Documentation

See [docs/WORKFLOW.md](WORKFLOW.md) for complete workflow documentation.

