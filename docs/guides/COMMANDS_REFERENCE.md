# A.V.A.R. Commands Reference

Quick reference for all available commands to run and test the system.

## 🚀 Quick Start

```bash
# One-command setup and launch
./quickstart.sh

# Or use make
make help    # See all available commands
```

## 📦 Docker Commands

### Start/Stop Services

```bash
# Start all services
make up
# Or: docker-compose up -d

# Stop all services
make down
# Or: docker-compose down

# Restart services
make restart
# Or: docker-compose restart

# Build containers
make build
# Or: docker-compose build

# View status
make status
# Or: docker-compose ps

# Check health
make health
```

### View Logs

```bash
# All services
make logs

# Specific service
make logs-ai           # AI Detection Service
make logs-gateway      # API Gateway
make logs-competition  # Competition Service (when implemented)
make logs-frontend     # Frontend (when implemented)

# Or directly:
docker-compose logs -f ai-detection-service
docker-compose logs -f api-gateway --tail=100
```

### Shell Access

```bash
# AI Detection Service shell
make shell-ai
# Or: docker-compose exec ai-detection-service /bin/bash

# PostgreSQL shell
make shell-db
# Or: docker-compose exec postgres psql -U avar_user -d avar_db

# Redis shell
make shell-redis
# Or: docker-compose exec redis redis-cli
```

## 🧪 Testing Commands

### Setup Tests

```bash
# Install test dependencies
make test-install
# Or: pip install -r tests/requirements.txt && playwright install chromium
```

### Run Tests

```bash
# Complete test suite
make test-all
# Or: ./tests/run_tests.sh all

# Unit tests only
make test-unit
# Or: ./tests/run_tests.sh unit

# Integration tests
make test-integration
# Or: ./tests/run_tests.sh integration

# End-to-end tests (browser)
make test-e2e
# Or: ./tests/run_tests.sh e2e

# Performance tests
make test-performance
# Or: ./tests/run_tests.sh performance

# Quick smoke tests (fast)
make test-quick
# Or: pytest tests/integration/ -v -m "not slow" --tb=short

# Coverage report
make test-coverage
# Or: ./tests/run_tests.sh coverage
```

### Specific Test Commands

```bash
# Run specific test file
pytest tests/integration/test_ai_detection_api.py -v

# Run specific test
pytest tests/integration/test_ai_detection_api.py::test_health_check -v

# Run with markers
pytest -m slow        # Only slow tests
pytest -m "not slow"  # Exclude slow tests
pytest -m integration # Only integration tests

# Verbose output
pytest tests/ -vv -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Parallel execution
pytest tests/ -n 4  # 4 parallel workers
```

### Performance Testing

```bash
# Headless performance test
make test-performance
# Or: locust -f tests/performance/locustfile.py --host=http://localhost:8001 --users 10 --spawn-rate 2 --run-time 60s --headless

# With web UI
make performance-ui
# Or: locust -f tests/performance/locustfile.py --host=http://localhost:8001
# Then open: http://localhost:8089

# Quick load test
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8001 \
  --users 5 \
  --spawn-rate 1 \
  --run-time 30s \
  --headless
```

## 🔧 Development Commands

### Local Development

```bash
# Install dependencies locally
make install

# Run AI Detection Service locally
make dev-ai
# Or: cd src/backend/ai-detection-service && uvicorn app.main:app --reload --port 8001

# Run API Gateway locally
make dev-gateway
# Or: cd src/backend/api-gateway && uvicorn app.main:app --reload --port 8000
```

### Code Quality

```bash
# Format code (if configured)
black src/backend/ai-detection-service/app/
black tests/

# Lint code
flake8 src/backend/ai-detection-service/app/
pylint src/backend/ai-detection-service/app/

# Type checking
mypy src/backend/ai-detection-service/app/

# Sort imports
isort src/backend/ai-detection-service/app/
```

## 🌐 API Testing Commands

### Health Checks

```bash
# Check all services
make health

# Manual checks
curl http://localhost:8001/health | python3 -m json.tool
curl http://localhost:8000/health | python3 -m json.tool
```

### Test API Endpoints

```bash
# Root endpoint
curl http://localhost:8001/

# Health check
curl http://localhost:8001/health

# Metadata-only analysis
curl -X POST http://localhost:8001/api/v1/analyze/metadata-only \
  -F "jpg_file=@test_image.jpg" \
  | python3 -m json.tool

# Full analysis
curl -X POST http://localhost:8001/api/v1/analyze \
  -F "jpg_file=@test_image.jpg" \
  | python3 -m json.tool

# With RAW file
curl -X POST http://localhost:8001/api/v1/analyze \
  -F "jpg_file=@photo.jpg" \
  -F "raw_file=@photo.cr3" \
  | python3 -m json.tool
```

### API Documentation

```bash
# Open API docs in browser
# Linux:
xdg-open http://localhost:8001/docs

# macOS:
open http://localhost:8001/docs

# Windows:
start http://localhost:8001/docs

# Or manually navigate to:
# http://localhost:8001/docs (AI Detection Service)
# http://localhost:8000/docs (API Gateway)
```

## 🐛 Debugging Commands

### Check Logs

```bash
# Tail logs
docker-compose logs -f ai-detection-service

# Last 100 lines
docker-compose logs --tail=100 ai-detection-service

# Follow logs with timestamp
docker-compose logs -f -t ai-detection-service

# Grep logs
docker-compose logs ai-detection-service | grep ERROR
```

### Debug Container

```bash
# Execute command in container
docker-compose exec ai-detection-service python3 --version
docker-compose exec ai-detection-service ls -la /app

# Check running processes
docker-compose exec ai-detection-service ps aux

# Check network
docker-compose exec ai-detection-service curl http://localhost:8001/health
```

### Database Debug

```bash
# Connect to PostgreSQL
make shell-db

# Inside psql:
\dt                    # List tables
\d submissions        # Describe table
SELECT * FROM submissions LIMIT 10;

# Check connections
SELECT * FROM pg_stat_activity;

# Database size
SELECT pg_size_pretty(pg_database_size('avar_db'));
```

### Redis Debug

```bash
# Connect to Redis
make shell-redis

# Inside redis-cli:
PING                  # Test connection
INFO                  # Server info
KEYS *                # List all keys (dev only!)
GET key_name          # Get value
FLUSHALL              # Clear all data (careful!)
```

## 📊 Monitoring Commands

### Resource Usage

```bash
# Docker stats
docker stats

# Specific container
docker stats avar-ai-detection

# Resource usage logs
docker-compose logs ai-detection-service | grep "memory\|cpu"
```

### Service Status

```bash
# All services
docker-compose ps

# Specific service
docker-compose ps ai-detection-service

# Detailed inspect
docker inspect avar-ai-detection
```

## 🧹 Cleanup Commands

### Clean Up

```bash
# Stop and remove containers
make down

# Remove containers and volumes (WARNING: Deletes data)
make clean
# Or: docker-compose down -v

# Remove dangling images
docker image prune

# Full cleanup (careful!)
docker system prune -a --volumes

# Remove test artifacts
rm -rf test-reports/ htmlcov/ .pytest_cache/
find . -type d -name __pycache__ -exec rm -rf {} +
```

## 📝 Git Commands

### Common Operations

```bash
# Check status
git status

# Add files
git add .

# Commit
git commit -m "Your message here"

# Push
git push origin main

# Pull latest
git pull origin main

# Create branch
git checkout -b feature/your-feature

# View logs
git log --oneline --graph

# View diff
git diff
```

## 🎯 One-Liners

### Quick Tests

```bash
# Test single endpoint
curl -s http://localhost:8001/health | python3 -c "import sys, json; print(f\"Status: {json.load(sys.stdin)['status']}\")"

# Generate test image and analyze
python3 -c "from PIL import Image; import numpy as np; Image.fromarray(np.random.randint(0,255,(800,600,3),dtype=np.uint8)).save('test.jpg')" && \
curl -X POST http://localhost:8001/api/v1/analyze -F "jpg_file=@test.jpg" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Verdict: {data['verdict']}, Confidence: {data['confidence_score']:.2%}\")"

# Count lines of code
find src -name "*.py" | xargs wc -l | tail -1

# Find TODO comments
grep -r "TODO" src/

# Check test coverage
pytest src/backend/ai-detection-service/tests/ --cov=app --cov-report=term | grep TOTAL
```

### Quick Status

```bash
# Everything at a glance
echo "=== Services ===" && docker-compose ps && \
echo -e "\n=== Health ===" && curl -s http://localhost:8001/health | python3 -c "import sys, json; print(f\"AI: {json.load(sys.stdin)['status']}\")" && \
curl -s http://localhost:8000/health | python3 -c "import sys, json; print(f\"Gateway: {json.load(sys.stdin)['status']}\")"
```

## 📚 Help Commands

```bash
# Make help
make help

# Docker compose help
docker-compose --help

# Pytest help
pytest --help

# Locust help
locust --help
```

## 🔗 URLs

When services are running:

```
AI Detection Service:
  http://localhost:8001
  http://localhost:8001/docs
  http://localhost:8001/health

API Gateway:
  http://localhost:8000
  http://localhost:8000/docs
  http://localhost:8000/health

Database (internal):
  postgres://avar_user:password@localhost:5432/avar_db

Redis (internal):
  redis://localhost:6379

Locust (when running):
  http://localhost:8089
```

## 💡 Pro Tips

```bash
# Watch logs and filter
docker-compose logs -f | grep -i error

# Restart specific service
docker-compose restart ai-detection-service

# Run test and save output
pytest tests/ -v | tee test-output.log

# Background service check
watch -n 5 'curl -s http://localhost:8001/health | python3 -m json.tool'

# Generate test report
pytest tests/ --html=report.html --self-contained-html

# Profile test performance
pytest tests/ --durations=10

# Debug test
pytest tests/test_file.py::test_name -vv -s --pdb
```

---

**Quick Reference Card**:

| Task | Command |
|------|---------|
| Start | `make up` or `./quickstart.sh` |
| Stop | `make down` |
| Test | `make test-all` |
| Logs | `make logs-ai` |
| Health | `make health` |
| Shell | `make shell-ai` |
| Clean | `make clean` |

**Full Documentation**: See [CLAUDE.md](CLAUDE.md), [TESTING_GUIDE.md](TESTING_GUIDE.md), and [README.md](README.md)
