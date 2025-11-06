# A.V.A.R. Testing Suite

Comprehensive testing framework for the A.V.A.R. AI Detection System.

## Test Structure

```
tests/
├── conftest.py                    # Global fixtures and configuration
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Testing dependencies
├── run_tests.sh                   # Automated test runner
├── fixtures/
│   └── images/                    # Test image samples
├── integration/
│   └── test_ai_detection_api.py  # API integration tests
├── e2e/
│   └── test_submission_workflow.py # Browser automation tests
└── performance/
    └── locustfile.py              # Load testing scenarios
```

## Quick Start

### 1. Install Test Dependencies

```bash
cd tests
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Start Services

```bash
# From project root
docker-compose up -d

# Wait for services to be ready
make health
```

### 3. Run Tests

```bash
# Run all tests
./tests/run_tests.sh all

# Or use make commands
make test          # Run all tests
make test-ai       # Run AI service tests only
make test-coverage # Run with coverage report
```

## Test Categories

### Unit Tests

Located in: `src/backend/ai-detection-service/tests/`

Tests individual components in isolation:
- Layer 1: Metadata Analysis
- Layer 2: Digital Fingerprint Analysis
- Layer 3: API Integration
- RAW-JPG Linkage
- Utility functions

```bash
# Run unit tests
./tests/run_tests.sh unit

# Or inside container
docker-compose exec ai-detection-service pytest tests/ -v
```

### Integration Tests

Located in: `tests/integration/`

Tests API endpoints and service interactions:
- `/health` endpoint
- `/api/v1/analyze` full pipeline
- `/api/v1/analyze/metadata-only` quick check
- Concurrent request handling
- Error handling

```bash
# Run integration tests
./tests/run_tests.sh integration

# Run specific test file
pytest tests/integration/test_ai_detection_api.py -v

# Run specific test
pytest tests/integration/test_ai_detection_api.py::TestLayer1MetadataAnalysis::test_ai_signature_detection -v
```

### End-to-End (E2E) Tests

Located in: `tests/e2e/`

Browser automation tests using Playwright:
- User registration and login
- Photo submission workflow
- Judge dashboard
- Admin quarantine review

```bash
# Run E2E tests
./tests/run_tests.sh e2e

# Run with visible browser (headed mode)
pytest tests/e2e/ --headed --browser chromium

# Run on different browsers
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit  # Safari engine
```

**Note:** E2E tests are currently skipped as frontend is not yet implemented.

### Performance Tests

Located in: `tests/performance/`

Load testing with Locust:
- Concurrent user simulation
- Throughput testing
- Response time analysis
- Breaking point identification

```bash
# Run performance tests (headless)
./tests/run_tests.sh performance

# Run with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8001

# Then open browser: http://localhost:8089

# Quick smoke test
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8001 \
    --users 5 \
    --spawn-rate 1 \
    --run-time 30s \
    --headless
```

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only slow tests
pytest -m slow

# Run all except slow tests
pytest -m "not slow"

# Run integration tests
pytest -m integration

# Run E2E tests
pytest -m e2e

# Run performance tests
pytest -m performance

# Combine markers
pytest -m "integration and not slow"
```

## Coverage Reports

```bash
# Generate coverage report
./tests/run_tests.sh coverage

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Coverage targets:
- **Overall**: > 80%
- **Critical paths** (detection layers): > 90%
- **Utilities**: > 70%

## Test Data

Test images are automatically generated in `tests/fixtures/images/`:

- `genuine_photo.jpg` - Realistic photo with sensor noise
- `genuine_with_exif.jpg` - Photo with camera metadata
- `ai_generated.jpg` - Smooth, AI-like image
- `ai_with_signature.jpg` - Image with AI metadata signature
- `corrupted.jpg` - Invalid/corrupted file

### Adding Custom Test Images

```python
# In your test file
def test_with_custom_image():
    image_path = FIXTURES_DIR / "my_test_image.jpg"
    # Test code here
```

## Continuous Integration

Tests run automatically on:
- Every commit (smoke tests)
- Every pull request (full suite)
- Nightly builds (including slow tests)

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Run tests
        run: ./tests/run_tests.sh all
```

## Debugging Tests

### View Logs

```bash
# Service logs
docker-compose logs -f ai-detection-service

# Test verbose output
pytest tests/ -vv --tb=long

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x
```

### Debug Specific Test

```bash
# Run single test with debugging
pytest tests/integration/test_ai_detection_api.py::test_name -vv -s

# Use pytest debugger
pytest tests/ --pdb  # Drop into debugger on failure
```

### Browser Debugging (Playwright)

```bash
# Run with slow motion
pytest tests/e2e/ --headed --slowmo 1000

# Run with debugging
PWDEBUG=1 pytest tests/e2e/

# Take screenshots on failure
pytest tests/e2e/ --screenshot on --video on
```

## Performance Benchmarks

Expected performance (on standard hardware):

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Layer 1 (Metadata) | < 200ms | < 1s |
| RAW-JPG Linkage | < 2s | < 5s |
| Layer 2 (PRNU) | < 5s | < 15s |
| Full Pipeline | < 10s | < 30s |
| Throughput | > 10 req/min | > 5 req/min |

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs

# Restart services
docker-compose restart

# Clean restart
docker-compose down && docker-compose up -d
```

### Tests Timing Out

```bash
# Increase timeout
pytest tests/ --timeout=600

# Or in pytest.ini:
# timeout = 600
```

### Import Errors

```bash
# Ensure you're in the right directory
cd tests

# Install test dependencies
pip install -r requirements.txt

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

### Playwright Issues

```bash
# Reinstall browsers
playwright install --force

# Clear cache
rm -rf ~/.cache/ms-playwright
playwright install
```

## Writing New Tests

### Unit Test Template

```python
import pytest
from app.services.my_service import MyService

@pytest.fixture
def service():
    return MyService()

def test_feature(service):
    """Test description"""
    result = service.do_something()
    assert result == expected_value
```

### Integration Test Template

```python
import pytest

BASE_URL = "http://localhost:8001"

def test_api_endpoint(api_client):
    """Test API endpoint"""
    response = api_client.get(f"{BASE_URL}/endpoint")

    assert response.status_code == 200
    data = response.json()
    assert "key" in data
```

### E2E Test Template

```python
import pytest
from playwright.sync_api import Page

@pytest.mark.e2e
def test_user_workflow(page: Page):
    """Test complete user workflow"""
    page.goto("http://localhost:3000")
    page.click("button.submit")
    assert page.locator(".success").is_visible()
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Fast Tests**: Keep unit tests under 1 second
3. **Clear Names**: Use descriptive test names
4. **Assertions**: Use specific assertions with clear messages
5. **Fixtures**: Reuse test data via fixtures
6. **Cleanup**: Always cleanup resources after tests
7. **Documentation**: Add docstrings to complex tests

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/python/)
- [Locust Documentation](https://docs.locust.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

## Support

For issues or questions:
- Check [CLAUDE.md](../CLAUDE.md) for development guidance
- Review test logs in `test-reports/`
- Contact: rasandilikshana@gmail.com
