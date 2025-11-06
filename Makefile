.PHONY: help build up down logs test clean restart test-all test-integration test-e2e test-performance

help:
	@echo "A.V.A.R. Development Commands"
	@echo "=============================="
	@echo "Docker Commands:"
	@echo "  make build           - Build all Docker containers"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make status          - Show service status"
	@echo "  make health          - Check service health"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test-install    - Install testing dependencies"
	@echo "  make test-all        - Run complete test suite"
	@echo "  make test-unit       - Run unit tests"
	@echo "  make test-integration- Run integration tests"
	@echo "  make test-e2e        - Run end-to-end browser tests"
	@echo "  make test-performance- Run performance/load tests"
	@echo "  make test-quick      - Run quick smoke tests"
	@echo "  make test-coverage   - Generate coverage report"
	@echo ""
	@echo "Development Commands:"
	@echo "  make logs            - View logs from all services"
	@echo "  make logs-ai         - View AI detection service logs"
	@echo "  make shell-ai        - Open shell in AI detection container"
	@echo "  make shell-db        - Open PostgreSQL shell"
	@echo "  make clean           - Clean up containers and volumes"
	@echo "  make install         - Install Python dependencies locally"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "AI Detection API: http://localhost:8001"
	@echo "API Gateway: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	@echo "Admin Panel: http://localhost:8080"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-ai:
	docker-compose logs -f ai-detection-service

logs-gateway:
	docker-compose logs -f api-gateway

logs-competition:
	docker-compose logs -f competition-service

logs-frontend:
	docker-compose logs -f frontend

test:
	docker-compose exec ai-detection-service pytest tests/ -v

test-ai:
	docker-compose exec ai-detection-service pytest tests/ -v --cov=app

test-coverage:
	docker-compose exec ai-detection-service pytest tests/ --cov=app --cov-report=html

clean:
	docker-compose down -v
	@echo "Cleaned up containers and volumes"

shell-ai:
	docker-compose exec ai-detection-service /bin/bash

shell-db:
	docker-compose exec postgres psql -U avar_user -d avar_db

shell-redis:
	docker-compose exec redis redis-cli

install:
	cd src/backend/ai-detection-service && pip install -r requirements.txt
	cd src/backend/api-gateway && pip install -r requirements.txt

dev-ai:
	cd src/backend/ai-detection-service && uvicorn app.main:app --reload --port 8001

dev-gateway:
	cd src/backend/api-gateway && uvicorn app.main:app --reload --port 8000

status:
	docker-compose ps

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Gateway unreachable"
	@curl -s http://localhost:8001/health | python3 -m json.tool || echo "AI Detection unreachable"

# Testing commands
test-install:
	@echo "Installing testing dependencies..."
	pip install -r tests/requirements.txt
	playwright install chromium

test-all:
	@echo "Running complete test suite..."
	./tests/run_tests.sh all

test-unit:
	@echo "Running unit tests..."
	./tests/run_tests.sh unit

test-integration:
	@echo "Running integration tests..."
	./tests/run_tests.sh integration

test-e2e:
	@echo "Running end-to-end tests..."
	./tests/run_tests.sh e2e

test-performance:
	@echo "Running performance tests..."
	./tests/run_tests.sh performance

test-quick:
	@echo "Running quick smoke tests..."
	pytest tests/integration/ -v -m "not slow" --tb=short

performance-ui:
	@echo "Starting Locust web UI..."
	locust -f tests/performance/locustfile.py --host=http://localhost:8001
