.PHONY: help build up down logs test clean restart

help:
	@echo "A.V.A.R. Development Commands"
	@echo "=============================="
	@echo "make build         - Build all Docker containers"
	@echo "make up            - Start all services"
	@echo "make down          - Stop all services"
	@echo "make restart       - Restart all services"
	@echo "make logs          - View logs from all services"
	@echo "make logs-ai       - View AI detection service logs"
	@echo "make logs-gateway  - View API gateway logs"
	@echo "make test          - Run all tests"
	@echo "make test-ai       - Run AI detection service tests"
	@echo "make clean         - Clean up containers and volumes"
	@echo "make shell-ai      - Open shell in AI detection container"
	@echo "make shell-db      - Open PostgreSQL shell"
	@echo "make install       - Install Python dependencies locally"

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
