.PHONY: setup install-dev seed test lint format run-api run-worker \
        run-scheduler run-collector run-demo docker-build docker-up docker-down \
        docker-logs clean health

PROJECT_DIR := $(shell pwd)
PYTHON      := python
PIP         := pip
export PYTHONPATH := $(PROJECT_DIR)
export DEMO_MODE ?= false
export DATABASE_URL ?= sqlite+aiosqlite:///./data/trading_intel.db

setup: install-dev seed
	@echo "Setup complete. Run 'make run-demo' to start."

install-dev:
	$(PIP) install -e ".[dev]"

seed:
	$(PYTHON) -m scripts.seed_demo_data

run-api:
	$(PYTHON) -m uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	$(PYTHON) -m apps.worker_service.main

run-scheduler:
	$(PYTHON) -m apps.scheduler_service.main

run-collector:
	$(PYTHON) -m apps.collector_service.main

run-demo:
	DEMO_MODE=true DATABASE_URL=$(DATABASE_URL) \
	$(PYTHON) -m uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000

test:
	DEMO_MODE=true DATABASE_URL=sqlite+aiosqlite:///./data/test_trading_intel.db \
	pytest tests/ -v --tb=short --cov=packages --cov-report=term-missing

test-unit:
	DEMO_MODE=true DATABASE_URL=sqlite+aiosqlite:///./data/test_trading_intel.db \
	pytest tests/unit/ -v --tb=short

test-integration:
	DEMO_MODE=true DATABASE_URL=sqlite+aiosqlite:///./data/test_trading_intel.db \
	pytest tests/integration/ -v --tb=short

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

docker-logs:
	docker-compose logs -f --tail=100

health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not running"

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build data/test_trading_intel.db
