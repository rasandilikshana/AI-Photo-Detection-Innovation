# Contributing to A.V.A.R.

Thank you for your interest in contributing to the A.V.A.R. (Aura Verification and Authentication for RAW files) project!

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project adheres to a code of conduct focused on:
- **Respectful communication**: Be kind and professional
- **Constructive feedback**: Focus on improvement, not criticism
- **Collaborative spirit**: We're all working toward the same goal
- **Academic integrity**: This is a research project - proper attribution is essential

## How Can I Contribute?

### Reporting Bugs
1. Check if the bug has already been reported in [Issues](https://github.com/rasandilikshana/avar/issues)
2. If not, create a new issue using the Bug Report template
3. Provide as much detail as possible (see the template for guidance)
4. Include logs, screenshots, and steps to reproduce

### Suggesting Enhancements
1. Check existing feature requests in [Issues](https://github.com/rasandilikshana/avar/issues)
2. Create a new issue using the Feature Request template
3. Clearly describe the problem and proposed solution
4. Explain why this enhancement would be useful

### Contributing Code
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write/update tests
5. Ensure all tests pass
6. Commit your changes (see commit message guidelines below)
7. Push to your fork
8. Open a Pull Request

## Development Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional but recommended)
- Git

### Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/avar.git
cd avar

# Add upstream remote
git remote add upstream https://github.com/rasandilikshana/avar.git

# Create virtual environment
cd src/backend/ai-detection-service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If it exists
pip install pytest pytest-cov black isort flake8 mypy pre-commit

# Install pre-commit hooks
cd ../../..
pre-commit install
```

### Running Locally

```bash
# Start services
./run_local.sh

# Or with Docker
docker-compose up -d

# Run tests
pytest tests/ -v

# Run specific tests
pytest tests/integration/test_ai_detection_api.py -v
```

## Coding Standards

### Python Code Style

We follow **PEP 8** with some modifications:
- **Line length**: 120 characters (not 79)
- **Formatter**: Black
- **Import sorting**: isort
- **Linting**: flake8
- **Type checking**: mypy (optional but encouraged)

### Automated Formatting

```bash
# Format code with Black
black src/backend/ai-detection-service/app/

# Sort imports
isort src/backend/ai-detection-service/app/

# Run linter
flake8 src/backend/ai-detection-service/app/

# Type checking
mypy src/backend/ai-detection-service/app/ --ignore-missing-imports
```

### Pre-commit Hooks

Pre-commit hooks automatically run before each commit:
```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Organization

- **One class per file** (generally)
- **Descriptive names**: `analyze_metadata()` not `am()`
- **Docstrings**: All public functions/classes need docstrings
- **Type hints**: Use where possible

Example:
```python
from typing import Dict, Optional

def analyze_metadata(image_path: str, raw_path: Optional[str] = None) -> Dict:
    """
    Analyze EXIF metadata from image files.

    Args:
        image_path: Path to JPG image file
        raw_path: Optional path to RAW file

    Returns:
        Dictionary containing analysis results with verdict and flags

    Raises:
        FileNotFoundError: If image file doesn't exist
    """
    # Implementation here
    pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # API/service integration tests
├── e2e/            # End-to-end browser tests
└── performance/    # Load/stress tests
```

### Writing Tests

```python
import pytest
from app.services.layer1_metadata import MetadataAnalyzer

@pytest.fixture
def analyzer():
    return MetadataAnalyzer()

def test_ai_signature_detection(analyzer):
    """Test that AI signatures are correctly identified"""
    metadata = {"Software": "Midjourney Bot"}

    ai_detected, flags = analyzer._detect_ai_signatures(metadata)

    assert ai_detected is True
    assert len(flags) > 0
    assert "midjourney" in flags[0].lower()
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Exclude slow tests

# With coverage
pytest tests/ --cov=app --cov-report=html

# Parallel execution
pytest tests/ -n 4      # 4 parallel workers
```

### Test Coverage

- **Minimum**: 70% overall
- **Critical paths** (detection layers): 90%+
- **New code**: Must have tests
- **Bug fixes**: Add regression test

## Pull Request Process

### Before Submitting

1. **Update from upstream**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all checks**
   ```bash
   # Format code
   black src/backend/ai-detection-service/app/
   isort src/backend/ai-detection-service/app/

   # Run tests
   pytest tests/ -v

   # Check linting
   flake8 src/backend/ai-detection-service/app/
   ```

3. **Update documentation**
   - Update CHANGELOG.md
   - Update relevant docs in `docs/`
   - Add/update docstrings

4. **Write good commit messages**
   ```
   feat: Add PRNU threshold auto-tuning

   - Implement adaptive threshold calculation
   - Add tests for edge cases
   - Update documentation

   Fixes #123
   ```

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Build process, dependencies

**Examples**:
```
feat: Add RAW-JPG linkage verification

Implement perceptual hash comparison between RAW and JPG files
to prevent submission forgery attacks.

Closes #45
```

```
fix: Correct PRNU threshold calculation

Previous threshold was too strict, causing false rejections.
Adjusted based on test data analysis.

Fixes #89
```

### Pull Request Checklist

- [ ] Code follows project style guidelines
- [ ] Self-reviewed my own code
- [ ] Commented hard-to-understand sections
- [ ] Updated documentation
- [ ] Added tests
- [ ] All tests pass locally
- [ ] No new warnings/errors
- [ ] Updated CHANGELOG.md

### Review Process

1. Automated CI checks must pass
2. At least one approval from project maintainer
3. All conversations resolved
4. Up-to-date with main branch

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR** (v2.0.0): Breaking changes
- **MINOR** (v1.1.0): New features, backwards-compatible
- **PATCH** (v1.0.1): Bug fixes, backwards-compatible

### Creating a Release

1. **Update version**
   ```bash
   # Update VERSION file
   echo "1.1.0" > VERSION

   # Update CHANGELOG.md
   # Add section for new version
   ```

2. **Create release commit**
   ```bash
   git commit -am "chore: Release v1.1.0"
   ```

3. **Create tag**
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

4. **GitHub Actions will automatically**:
   - Run full test suite
   - Build Docker images
   - Create GitHub release
   - Publish artifacts

## Development Workflow

### Feature Branch Workflow

```bash
# 1. Update main
git checkout main
git pull upstream main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and commit
git add .
git commit -m "feat: Add my feature"

# 4. Push to your fork
git push origin feature/my-feature

# 5. Create Pull Request on GitHub
```

### Keeping Fork Updated

```bash
# Add upstream if not already added
git remote add upstream https://github.com/rasandilikshana/avar.git

# Fetch and merge
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Questions?

- Check the [documentation](docs/README.md)
- Review existing [issues](https://github.com/rasandilikshana/avar/issues)
- Contact: rasandilikshana@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (Academic Research Project).

---

Thank you for contributing to A.V.A.R.! Your efforts help advance research in photography competition integrity. 🚀
