# GitHub Repository Setup Guide

Complete guide for pushing your A.V.A.R. project to GitHub with CI/CD automation.

## Prerequisites

- Git installed locally
- GitHub account created
- SSH key configured (recommended) or HTTPS credentials

## Step 1: Create GitHub Repository

### Option A: Via GitHub Web Interface

1. Go to [github.com](https://github.com)
2. Click "+" → "New repository"
3. Enter repository name: `avar` or `ai-photo-detection`
4. Add description: "AI-Powered Authenticity Verification System for Photography Competitions"
5. Choose visibility:
   - **Public**: Recommended for dissertation/portfolio
   - **Private**: For development only
6. **DO NOT** initialize with README (we have one)
7. Click "Create repository"

### Option B: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# Linux: sudo apt install gh
# macOS: brew install gh
# Windows: choco install gh

# Login
gh auth login

# Create repository
gh repo create avar --public \
  --description "AI-Powered Authenticity Verification System for Photography Competitions" \
  --source=.
```

## Step 2: Prepare Local Repository

```bash
# Navigate to project directory
cd "/media/rasan/windows-drive/NPAS/NPAS - Third Year/Rasan Research 3"

# Verify git is initialized
git status

# If not initialized:
git init
git config user.name "rasandilikshana"
git config user.email "rasandilikshana@gmail.com"

# Set default branch to main (if needed)
git branch -M main
```

## Step 3: Clean Up Before First Commit

```bash
# Remove temporary files (already done)
# Verify .gitignore is correct
cat .gitignore

# Remove any remaining temporary files
rm -rf /tmp/avar* 2>/dev/null || true
rm -rf __pycache__ .pytest_cache htmlcov 2>/dev/null || true

# Check what will be committed
git status
```

## Step 4: Initial Commit

```bash
# Add all files
git add .

# Review what's being added
git status

# Create initial commit
git commit -m "$(cat <<'EOF'
feat: Initial commit - A.V.A.R. v1.0.0

Comprehensive AI-powered authenticity verification system for photography
competitions with multi-layer detection pipeline.

Features:
- Layer 1: EXIF Metadata Analysis
- Layer 2: Digital Fingerprint (PRNU, ELA, FFT)
- Layer 3: Third-Party API Integration
- RAW-JPG Linkage Verification (world's first)
- Comprehensive testing suite (80%+ coverage)
- Complete documentation (3,500+ lines)
- CI/CD pipeline (GitHub Actions)
- Docker containerization

Tech Stack:
- Python 3.12, FastAPI, OpenCV, PyWavelets
- PostgreSQL, Redis
- Docker, GitHub Actions
- Pytest, Playwright, Locust

Research Project: NPAS Third Year Dissertation
Author: Rasan Dilikshana

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

## Step 5: Add Remote and Push

```bash
# Add GitHub remote (replace USERNAME with your GitHub username)
git remote add origin https://github.com/rasandilikshana/avar.git

# Or with SSH:
# git remote add origin git@github.com:rasandilikshana/avar.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main
```

## Step 6: Create First Release

```bash
# Create and push tag
git tag -a v1.0.0 -m "Release v1.0.0 - Production Ready

First production release of A.V.A.R. system.

Features:
- Complete AI detection pipeline
- Comprehensive testing suite
- Full documentation
- CI/CD automation

Ready for dissertation submission and production deployment.
"

# Push tag (triggers release workflow)
git push origin v1.0.0
```

## Step 7: Configure GitHub Repository Settings

### Enable GitHub Actions

1. Go to repository → Settings → Actions → General
2. Select "Allow all actions and reusable workflows"
3. Enable "Read and write permissions" for GITHUB_TOKEN
4. Save

### Enable GitHub Pages (Optional)

1. Go to Settings → Pages
2. Source: Deploy from branch
3. Branch: `main`, folder: `/docs`
4. Save

### Add Repository Topics

1. Go to repository main page
2. Click "⚙️" next to "About"
3. Add topics:
   - `ai`
   - `computer-vision`
   - `photography`
   - `forensics`
   - `python`
   - `fastapi`
   - `docker`
   - `testing`
   - `dissertation`
   - `research`

### Configure Branch Protection (Recommended)

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass
   - ✅ Require conversation resolution
   - ✅ Do not allow bypassing the above settings

## Step 8: Verify CI/CD Pipeline

### Check Workflows

1. Go to repository → Actions tab
2. You should see:
   - ✅ CI - Continuous Integration
   - ✅ Release - Automated Deployment
   - ✅ Cleanup - Remove Old Artifacts

### First CI Run

After pushing, CI will automatically run:
- Code quality checks
- Unit tests
- Integration tests
- Security scanning
- Docker build
- Documentation check

Monitor at: `https://github.com/rasandilikshana/avar/actions`

## Step 9: Set Up Secrets (If Needed)

For third-party API integration:

1. Go to Settings → Secrets and variables → Actions
2. Add secrets:
   - `HIVE_AI_API_KEY`: Your Hive AI API key
   - `DOCKER_USERNAME`: Docker Hub username (if using)
   - `DOCKER_PASSWORD`: Docker Hub token (if using)

## Step 10: Update README Badges

Add badges to README.md:

```markdown
# A.V.A.R. - Aura Verification and Authentication for RAW files

![Build Status](https://github.com/rasandilikshana/avar/workflows/CI/badge.svg)
![License](https://img.shields.io/badge/license-Academic%20Research-blue)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Coverage](https://codecov.io/gh/rasandilikshana/avar/branch/main/graph/badge.svg)

**AI-Powered Authenticity Verification System for Photography Competitions**
```

## Daily Development Workflow

### Making Changes

```bash
# 1. Pull latest changes
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and test
# ... code changes ...
pytest tests/ -v

# 4. Commit changes
git add .
git commit -m "feat: Add your feature

Detailed description of changes.

Fixes #issue-number"

# 5. Push to GitHub
git push origin feature/your-feature-name

# 6. Create Pull Request on GitHub
# Visit: https://github.com/rasandilikshana/avar/pulls
# Click "New Pull Request"
```

### Creating Releases

```bash
# 1. Update VERSION file
echo "1.1.0" > VERSION

# 2. Update CHANGELOG.md
# Add section for v1.1.0

# 3. Commit changes
git commit -am "chore: Release v1.1.0"

# 4. Create tag
git tag -a v1.1.0 -m "Release v1.1.0"

# 5. Push
git push origin main
git push origin v1.1.0

# GitHub Actions will automatically:
# - Build Docker images
# - Run tests
# - Create GitHub release
# - Upload artifacts
```

## Troubleshooting

### Push Rejected

```bash
# If push is rejected due to outdated local branch
git pull --rebase origin main
git push origin main
```

### Authentication Failed (HTTPS)

```bash
# Use Personal Access Token instead of password
# Generate token: GitHub → Settings → Developer settings → Personal access tokens
# Use token as password when prompted
```

### CI Build Failing

1. Check Actions tab for error details
2. Run tests locally: `pytest tests/ -v`
3. Fix issues and push again
4. CI will automatically re-run

### Large File Error

```bash
# If you accidentally added large files
git rm --cached path/to/large/file
git commit --amend
git push --force origin branch-name
```

## Best Practices

### Commit Messages

✅ Good:
```
feat: Add PRNU threshold auto-tuning

Implement adaptive threshold calculation based on image
characteristics to reduce false positives.

Fixes #123
```

❌ Bad:
```
updated stuff
```

### Branch Naming

- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/what-changed` - Documentation only
- `refactor/what-refactored` - Code refactoring
- `test/what-tested` - Test additions

### Pull Requests

1. **Small, focused PRs** - One feature/fix per PR
2. **Good descriptions** - Explain what and why
3. **Link issues** - Use "Fixes #123"
4. **Update docs** - Keep documentation current
5. **Add tests** - Test your changes

## GitHub Features to Use

### Issues
- Track bugs and feature requests
- Use labels: `bug`, `enhancement`, `documentation`
- Use milestones for versions
- Link to PRs and commits

### Projects (Optional)
- Create project board for task management
- Columns: To Do, In Progress, Done
- Track dissertation timeline

### Discussions (Optional)
- Research questions
- Implementation discussions
- Architecture decisions

### Wiki (Optional)
- Extended documentation
- Tutorials
- FAQ

## Continuous Integration Status

After setup, your repository will have:

✅ **Automated Testing**
- Runs on every push
- Runs on every pull request
- Tests all supported Python versions

✅ **Code Quality Checks**
- Black formatting
- isort import sorting
- flake8 linting
- mypy type checking

✅ **Security Scanning**
- Dependency vulnerability checks
- Bandit security linting
- Secret detection

✅ **Automated Releases**
- Triggered by version tags
- Builds Docker images
- Creates GitHub releases
- Publishes artifacts

✅ **Documentation**
- Link checking
- Structure validation
- Auto-generated API docs

## Monitoring Your Repository

### GitHub Insights

Check regularly:
- **Traffic**: Views, clones, referrers
- **Community**: Issues, PRs, discussions
- **Dependencies**: Dependency graph, alerts

### Notifications

Configure at: Settings → Notifications
- Watch releases only (recommended)
- Or watch all activity

## Resources

- [GitHub Docs](https://docs.github.com)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Git Best Practices](https://git-scm.com/book/en/v2)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Quick Reference**:

```bash
# Daily workflow
git pull origin main
git checkout -b feature/my-feature
# ... make changes ...
git add .
git commit -m "feat: Description"
git push origin feature/my-feature
# Create PR on GitHub

# Release
echo "1.1.0" > VERSION
git commit -am "chore: Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

---

**Setup Complete!** 🎉

Your repository is now:
- ✅ On GitHub
- ✅ CI/CD enabled
- ✅ Properly configured
- ✅ Ready for collaboration

**Repository URL**: `https://github.com/rasandilikshana/avar`
