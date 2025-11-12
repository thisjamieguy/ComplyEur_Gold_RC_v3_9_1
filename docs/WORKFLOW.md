# Developer Workflow – ComplyEur

This document outlines the professional branching, versioning, and release workflow for the ComplyEur project. Following these guidelines ensures consistent, traceable releases and maintains code quality.

---

## 📋 Table of Contents

- [Branch Architecture](#branch-architecture)
- [Version Control](#version-control)
- [Feature Development Workflow](#feature-development-workflow)
- [Release Workflow](#release-workflow)
- [Automation Scripts](#automation-scripts)
- [Best Practices](#best-practices)

---

## 🌳 Branch Architecture

### Persistent Branches

- **`main`** → Production-ready code only
  - Protected from direct commits
  - Requires pull requests from `develop`
  - Automatically triggers GitHub Releases on merge

- **`develop`** → Integration and testing branch
  - Default branch for feature integration
  - All feature branches merge here first
  - Continuous integration runs on every push

### Feature Branches

Format: `feature/<short_description>`

Examples:
- `feature/calendar_resizing`
- `feature/export_enhancements`
- `feature/gdpr_audit_tools`

### Release Branches

Format: `release/<version>`

Examples:
- `release/3.10.0`
- `release/3.11.0`

Used for preparing releases, final testing, and version bumping.

---

## 🔢 Version Control

### Semantic Versioning

ComplyEur follows [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH):

- **MAJOR** (X.0.0): Breaking changes, major feature additions
- **MINOR** (x.X.0): New features, backwards-compatible
- **PATCH** (x.x.X): Bug fixes, minor improvements

### Version File

The `VERSION` file is the single source of truth for the current version:

```
3.9.1
```

Additional metadata can be included on subsequent lines, but the first line must contain the semantic version.

---

## 🚀 Feature Development Workflow

### 1. Create a Feature Branch

```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your_feature_name
```

### 2. Develop and Commit

Work normally, commit often with clear messages:

```bash
# Use conventional commit messages
git commit -m "feat: add calendar drag-and-drop"
git commit -m "fix: resolve timezone display issue"
git commit -m "docs: update API documentation"
```

**Conventional Commit Prefixes:**
- `feat:` / `add:` - New features
- `fix:` / `bugfix:` - Bug fixes
- `change:` / `refactor:` - Code changes/refactoring
- `security:` - Security improvements
- `docs:` - Documentation updates
- `chore:` - Maintenance tasks

### 3. Push and Create Pull Request

```bash
git push origin feature/your_feature_name
```

Create a pull request from `feature/your_feature_name` → `develop` on GitHub.

### 4. Code Review and Merge

- Reviewers check the PR
- CI/CD runs automated tests
- Once approved, merge to `develop`
- Delete the feature branch after merge

---

## 📦 Release Workflow

### Preparing a Release

When `develop` is stable and ready for production:

#### Step 1: Create Release Branch

```bash
git checkout develop
git pull origin develop
git checkout -b release/3.10.0
```

#### Step 2: Bump Version

```bash
# For minor release (new features)
./scripts/bump_version.sh minor

# For patch release (bug fixes)
./scripts/bump_version.sh patch

# For major release (breaking changes)
./scripts/bump_version.sh major
```

This script:
- Reads current version from `VERSION`
- Increments based on argument
- Updates `VERSION` file
- Commits with message: `chore: bump version to X.Y.Z`
- Creates Git tag: `vX.Y.Z`
- Pushes commit and tag to GitHub

#### Step 3: Update Changelog

```bash
./scripts/update_changelog.sh
```

This script:
- Finds commits since last tag
- Categorises by type (Added, Fixed, Changed, etc.)
- Prepends formatted entry to `CHANGELOG.md`
- Commits with message: `docs: update CHANGELOG for vX.Y.Z`

#### Step 4: Final Testing

Run comprehensive tests:

```bash
# Python tests
pytest tests/ -v

# Playwright tests
npx playwright test

# Security checks
./scripts/run_security_checks.sh
```

#### Step 5: Merge to Main

```bash
git checkout main
git pull origin main
git merge release/3.10.0
git push origin main
```

#### Step 6: GitHub Release (Automatic)

When code is pushed to `main` with a version tag, GitHub Actions automatically:
- Runs test suite
- Extracts changelog section
- Creates GitHub Release with tag and release notes

You can also trigger manually via GitHub Actions → "Version Release" → "Run workflow".

---

## 🛠️ Automation Scripts

### `scripts/bump_version.sh`

Bumps version and creates Git tag.

**Usage:**
```bash
./scripts/bump_version.sh [major|minor|patch]
```

**Example:**
```bash
./scripts/bump_version.sh minor
# Output: 3.9.1 → 3.10.0
```

**What it does:**
1. Validates version type argument
2. Reads current version from `VERSION`
3. Increments version accordingly
4. Updates `VERSION` file
5. Commits: `chore: bump version to X.Y.Z`
6. Creates tag: `vX.Y.Z`
7. Pushes to origin

### `scripts/update_changelog.sh`

Generates changelog entries from Git commits.

**Usage:**
```bash
./scripts/update_changelog.sh
```

**What it does:**
1. Finds latest Git tag
2. Extracts commits since that tag
3. Categorises by conventional commit prefix
4. Formats according to Keep a Changelog
5. Prepends to `CHANGELOG.md`
6. Commits: `docs: update CHANGELOG for vX.Y.Z`

---

## ✅ Best Practices

### Commit Messages

Use conventional commit format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Good examples:**
- `feat: add employee search functionality`
- `fix: resolve calendar date calculation bug`
- `security: update password hashing to Argon2id`
- `docs: update installation instructions`

**Bad examples:**
- `fixed bug`
- `update`
- `WIP`

### Branch Naming

- ✅ `feature/calendar_resizing`
- ✅ `release/3.10.0`
- ✅ `fix/login_redirect`
- ❌ `new-feature`
- ❌ `release-v3.10.0`
- ❌ `bugfix`

### Version Bumping

- **Patch** (3.9.1 → 3.9.2): Bug fixes, minor improvements
- **Minor** (3.9.1 → 3.10.0): New features, backwards-compatible
- **Major** (3.9.1 → 4.0.0): Breaking changes, major rewrites

### Testing Before Release

Always run full test suite before merging to `main`:

```bash
# Python unit tests
pytest tests/ -v

# Playwright E2E tests
npx playwright test

# Security audit
./scripts/run_security_checks.sh

# Manual smoke test
python run_local.py
# Visit http://localhost:5000 and verify core functionality
```

### Changelog Maintenance

- Keep changelog entries clear and user-focused
- Group related changes
- Include migration notes for breaking changes
- Update changelog before every release

---

## 🔒 Branch Protection

The `main` branch is protected with the following rules:

- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ❌ Block direct pushes
- ❌ Block force pushes

All changes to `main` must come via pull request from `develop` or `release/*` branches.

---

## 📝 Quick Reference

### Daily Workflow

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/my_feature
# ... work and commit ...
git push origin feature/my_feature
# Create PR: feature/my_feature → develop
```

### Release Workflow

```bash
# Prepare release
git checkout develop
git checkout -b release/3.10.0
./scripts/bump_version.sh minor
./scripts/update_changelog.sh
# Test thoroughly
git checkout main
git merge release/3.10.0
git push origin main
# GitHub Actions creates release automatically
```

### Emergency Hotfix

```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/3.9.2
# Fix bug
./scripts/bump_version.sh patch
./scripts/update_changelog.sh
git checkout main
git merge hotfix/3.9.2
git push origin main
# Also merge back to develop
git checkout develop
git merge hotfix/3.9.2
git push origin develop
```

---

## 🆘 Troubleshooting

### Script Permission Errors

If scripts aren't executable:

```bash
chmod +x scripts/bump_version.sh
chmod +x scripts/update_changelog.sh
```

### Version Parse Errors

Ensure `VERSION` file first line is pure semantic version:

```
3.9.1
```

Not:
```
3.9.1 – Gold Release Candidate
```

(Note: The script handles this, but pure version is preferred)

### Tag Already Exists

If tag already exists, delete it:

```bash
git tag -d v3.10.0
git push origin :refs/tags/v3.10.0
```

Then re-run `bump_version.sh`.

---

## 📚 Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Flow](https://nvie.com/posts/a-successful-git-branching-model/)

---

**Last Updated:** 2025-11-12  
**Maintained by:** ComplyEur Development Team

