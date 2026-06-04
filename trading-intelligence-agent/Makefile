.PHONY: setup install-dev emulator seed test lint format run-api run-worker \
        run-scheduler run-collector run-demo docker-build docker-up docker-down \
        docker-logs clean health

PROJECT_DIR := $(shell pwd)
PYTHON      := python
PIP         := pip
export PYTHONPATH := $(PROJECT_DIR)
export DEMO_MODE  := true

# ── Bootstrap ────────────────────────────────────────────────────────────────

setup: install-dev seed
	@echo "✓ Setup complete. Run 'make run-demo' to start."

install-dev:
	$(PIP) install -e ".[dev]"

# Seed demo data (requires emulator running, or DEMO_MODE=true)
seed:
	DEMO_MODE=true $(PYTHON) -m scripts.seed_demo_data

# ── Firebase Emulator ─────────────────────────────────────────────────────────
# Requires: npm install -g firebase-tools  (one-time)
emulator:
	firebase emulators:start --only firestore --project demo-trading-intel

emulator-bg:
	firebase emulators:start --only firestore --project demo-trading-intel &

# ── Local services ────────────────────────────────────────────────────────────

run-api:
	uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	$(PYTHON) -m apps.worker_service.main

run-scheduler:
	$(PYTHON) -m apps.scheduler_service.main

run-collector:
	$(PYTHON) -m apps.collector_service.main

# Demo mode: uses Firebase emulator, no real API keys needed
run-demo:
	FIRESTORE_EMULATOR_HOST=localhost:8080 FIREBASE_PROJECT_ID=demo-trading-intel \
	uvicorn apps.api_service.main:app --reload --host 0.0.0.0 --port 8000

# ── Quality ───────────────────────────────────────────────────────────────────

test:
	DEMO_MODE=true FIRESTORE_EMULATOR_HOST=localhost:8080 FIREBASE_PROJECT_ID=demo-trading-intel \
	pytest tests/ -v --tb=short --cov=packages --cov-report=term-missing

test-unit:
	DEMO_MODE=true pytest tests/unit/ -v --tb=short

test-integration:
	DEMO_MODE=true FIRESTORE_EMULATOR_HOST=localhost:8080 FIREBASE_PROJECT_ID=demo-trading-intel \
	pytest tests/integration/ -v --tb=short

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .
	ruff check --fix .

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down -v

docker-logs:
	docker-compose logs -f --tail=100

# ── Utilities ─────────────────────────────────────────────────────────────────

health:
	@curl -s http://localhost:8000/health | python -m json.tool || echo "API not running"

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov dist build
