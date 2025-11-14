.PHONY: help setup install install-dev env run dev test test-v lint format check-format check-syntax push-check docker-up docker-down docker-rebuild clean

# Python interpreter
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)EduScale Engine - Available Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

setup: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)Virtual environment created at $(VENV)$(NC)"
	@echo "$(YELLOW)Run 'source $(VENV)/bin/activate' to activate it$(NC)"

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

install-dev: install ## Install dependencies including dev tools (linters, formatters)
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	$(BIN)/pip install black flake8 ruff mypy pytest-cov
	@echo "$(GREEN)Development dependencies installed successfully$(NC)"

env: ## Create .env file from .env.example
	@if [ ! -f .env ]; then \
		echo "$(BLUE)Creating .env file...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN).env file created$(NC)"; \
		echo "$(YELLOW)Please edit .env and configure your environment variables$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists$(NC)"; \
	fi

run: ## Run the application locally (production mode)
	@echo "$(BLUE)Starting EduScale Engine...$(NC)"
	$(BIN)/uvicorn eduscale.main:app --host 0.0.0.0 --port 8000

dev: ## Run the application locally with hot reload (development mode)
	@echo "$(BLUE)Starting EduScale Engine in development mode...$(NC)"
	$(BIN)/uvicorn eduscale.main:app --reload --host 0.0.0.0 --port 8000

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	$(BIN)/pytest

test-v: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	$(BIN)/pytest -v

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(BIN)/pytest --cov=eduscale --cov-report=html --cov-report=term

lint: ## Run linter (ruff and flake8)
	@echo "$(BLUE)Running linters...$(NC)"
	@if [ -f $(BIN)/ruff ]; then \
		$(BIN)/ruff check src/; \
	else \
		echo "$(YELLOW)Ruff not installed. Run 'make install-dev' to install dev tools$(NC)"; \
	fi
	@if [ -f $(BIN)/flake8 ]; then \
		$(BIN)/flake8 src/ --max-line-length=120 --extend-ignore=E203,W503; \
	else \
		echo "$(YELLOW)Flake8 not installed. Run 'make install-dev' to install dev tools$(NC)"; \
	fi

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@if [ -f $(BIN)/black ]; then \
		$(BIN)/black src/ tests/; \
		echo "$(GREEN)Code formatted successfully$(NC)"; \
	else \
		echo "$(YELLOW)Black not installed. Run 'make install-dev' to install dev tools$(NC)"; \
	fi

check-format: ## Check code formatting without modifying files
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@if [ -f $(BIN)/black ]; then \
		$(BIN)/black --check src/ tests/; \
	else \
		echo "$(YELLOW)Black not installed. Run 'make install-dev' to install dev tools$(NC)"; \
	fi

check-syntax: ## Check Python syntax without running
	@echo "$(BLUE)Checking Python syntax...$(NC)"
	@$(PYTHON) -m py_compile src/eduscale/**/*.py 2>/dev/null || \
		find src/eduscale -name "*.py" -exec $(PYTHON) -m py_compile {} \; 2>&1 | grep -v "Skipping" || true
	@echo "$(GREEN)Syntax check completed$(NC)"

check-types: ## Run type checking with mypy
	@echo "$(BLUE)Running type checking...$(NC)"
	@if [ -f $(BIN)/mypy ]; then \
		$(BIN)/mypy src/eduscale --ignore-missing-imports; \
	else \
		echo "$(YELLOW)Mypy not installed. Run 'make install-dev' to install dev tools$(NC)"; \
	fi

check-git: ## Check git status for uncommitted changes
	@echo "$(BLUE)Checking git status...$(NC)"
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "$(YELLOW)Warning: You have uncommitted changes:$(NC)"; \
		git status --short; \
		echo ""; \
	else \
		echo "$(GREEN)Working directory clean$(NC)"; \
	fi

push-check: ## Run all checks before pushing (git status, syntax, tests)
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  Running pre-push checks...$(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@echo "$(BLUE)[1/3] Checking git status...$(NC)"
	@$(MAKE) check-git
	@echo ""
	@echo "$(BLUE)[2/3] Checking Python syntax...$(NC)"
	@$(MAKE) check-syntax
	@echo ""
	@echo "$(BLUE)[3/3] Running tests...$(NC)"
	@$(MAKE) test
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  ✓ All checks passed!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(YELLOW)Ready to push to remote repository$(NC)"

docker-up: ## Start development environment with Docker Compose
	@echo "$(BLUE)Starting Docker Compose...$(NC)"
	docker compose -f docker/docker-compose.dev.yml up

docker-up-d: ## Start development environment with Docker Compose in background
	@echo "$(BLUE)Starting Docker Compose in background...$(NC)"
	docker compose -f docker/docker-compose.dev.yml up -d

docker-down: ## Stop Docker Compose environment
	@echo "$(BLUE)Stopping Docker Compose...$(NC)"
	docker compose -f docker/docker-compose.dev.yml down

docker-rebuild: ## Rebuild and start Docker Compose environment
	@echo "$(BLUE)Rebuilding Docker Compose...$(NC)"
	docker compose -f docker/docker-compose.dev.yml up --build

docker-logs: ## Show Docker Compose logs
	docker compose -f docker/docker-compose.dev.yml logs -f

docker-build-tabular: ## Build tabular service image with BuildKit (optimized)
	@echo "$(BLUE)Building tabular service with BuildKit...$(NC)"
	DOCKER_BUILDKIT=1 docker build \
		-f docker/Dockerfile.tabular \
		-t tabular-service:latest \
		.
	@echo "$(GREEN)Tabular service built successfully$(NC)"

docker-build-tabular-cache: ## Build tabular service with BuildKit and cache (fastest)
	@echo "$(BLUE)Building tabular service with BuildKit and cache...$(NC)"
	DOCKER_BUILDKIT=1 docker build \
		--cache-from tabular-service:latest \
		-f docker/Dockerfile.tabular \
		-t tabular-service:latest \
		.
	@echo "$(GREEN)Tabular service built successfully$(NC)"

clean: ## Clean up temporary files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed$(NC)"

clean-all: clean ## Clean everything including virtual environment
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)Full cleanup completed$(NC)"

init: setup install env ## Initialize project (setup + install + env)
	@echo "$(GREEN)Project initialized successfully!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Activate virtual environment: source $(VENV)/bin/activate"
	@echo "  2. Edit .env file with your configuration"
	@echo "  3. Run 'make dev' to start development server"

# Quick shortcuts
.PHONY: t d pc
t: test ## Shortcut for 'test'
d: dev ## Shortcut for 'dev'
pc: push-check ## Shortcut for 'push-check'
