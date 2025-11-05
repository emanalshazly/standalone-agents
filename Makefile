# Makefile for Standalone Agents

.PHONY: help install install-dev test lint format clean run-api docs

help:
	@echo "Standalone Agents - Makefile Commands"
	@echo "======================================="
	@echo "install          Install production dependencies"
	@echo "install-dev      Install development dependencies"
	@echo "test             Run tests"
	@echo "test-cov         Run tests with coverage"
	@echo "lint             Run linters"
	@echo "format           Format code"
	@echo "clean            Clean build artifacts"
	@echo "run-api          Run FastAPI server"
	@echo "docs             Build documentation"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term tests/

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/ examples/
	isort src/ tests/ examples/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

docs:
	mkdocs build

serve-docs:
	mkdocs serve
