# Video Duplicate Scanner CLI - Development Makefile

.PHONY: help install install-dev test test-unit test-integration test-contract lint format type-check clean

help: ## Show this help message
	@echo "Video Duplicate Scanner CLI - Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

install: ## Install the package
	pip install -e .

install-dev: ## Install the package with development dependencies
	pip install -e ".[dev]"

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/ -m unit

test-integration: ## Run integration tests only
	pytest tests/integration/ -m integration

test-contract: ## Run contract tests only
	pytest tests/contract/ -m contract

test-coverage: ## Run tests with coverage report
	pytest --cov-report=html --cov-report=term

lint: ## Run code linting
	flake8 src/ tests/
	black --check src/ tests/

format: ## Format code with black
	black src/ tests/

type-check: ## Run type checking with mypy
	mypy src/

clean: ## Clean up generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

version-check: ## Check Python version compatibility
	python src/lib/version_check.py