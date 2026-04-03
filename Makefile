# CodeReborn Engine — Makefile

# Variables
PYTHON = python3.11
PIP = $(PYTHON) -m pip
DOCKER_COMPOSE = docker compose
PATH_TO_ANALYZE ?= .
DB_URL = postgresql+asyncpg://postgres:postgres@localhost:5432/codereborn

.PHONY: help setup infra-up infra-down demo analyze clean

help:
	@echo "🚀 CodeReborn Engine — CLI"
	@echo "Usage:"
	@echo "  make setup          Install dependencies and create .env"
	@echo "  make infra-up       Start PostgreSQL and Redis"
	@echo "  make infra-down     Stop all containers"
	@echo "  make demo           Analyze this repository (default)"
	@echo "  make analyze        Analyze a custom path (use PATH_TO_ANALYZE=...)"
	@echo "  make clean          Remove temporary files"

setup:
	@echo "[*] Installing dependencies..."
	$(PIP) install -e .
	@if [ ! -f .env ]; then cp .env.example .env; echo "[OK] Created .env from example"; fi

infra-up:
	@echo "[*] Starting infrastructure (PostgreSQL, Redis)..."
	$(DOCKER_COMPOSE) up -d
	@echo "[OK] Containers are running."

infra-down:
	@echo "[*] Stopping infrastructure..."
	$(DOCKER_COMPOSE) down

demo:
	@echo "[*] Running StackDetector Demo..."
	DATABASE_URL=$(DB_URL) PYTHONPATH=. $(PYTHON) scripts/run_stack_detector.py --path .

analyze:
	@echo "[*] Analyzing path: $(PATH_TO_ANALYZE)"
	DATABASE_URL=$(DB_URL) PYTHONPATH=. $(PYTHON) scripts/run_stack_detector.py --path $(PATH_TO_ANALYZE) $(if $(JSON),--json)

clean:
	@echo "[*] Cleaning up temporary files..."
	rm -rf tmp/*.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
