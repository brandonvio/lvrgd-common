SHELL := /bin/bash
.PHONY: help install test test-verbose test-mongodb test-coverage clean lint format check

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies using uv"
	@echo "  test         - Run all unit tests"
	@echo "  test-verbose - Run all unit tests with verbose output"
	@echo "  test-mongodb - Run MongoDB service tests only"
	@echo "  test-coverage- Run tests with coverage report"
	@echo "  lint         - Run code linting"
	@echo "  format       - Format code"
	@echo "  check        - Run all checks (lint, format, test)"
	@echo "  clean        - Clean up temporary files"

validate:
	@echo "Validating code..."
	ruff check . --fix
	ruff format .
	uv run python -m pytest tests/ -x --tb=short

# Install dependencies
install:
	@echo "Installing dependencies with uv..."
	uv sync

# Run all unit tests
test:
	@echo "Running unit tests..."
	uv run python -m pytest tests/ -x

test-short:
	@echo "Running short unit tests..."
	uv run python -m pytest tests/ -v --tb=short

# Run tests with verbose output
test-verbose:
	@echo "Running unit tests with verbose output..."
	uv run python -m pytest tests/ -v

# Run MongoDB service tests only
test-mongodb:
	@echo "Running MongoDB service tests..."
	uv run python -m pytest tests/mongodb/ -v

# Run tests with coverage
test-coverage:
	@echo "Running unit tests with coverage..."
	uv run python -m pytest tests/ --cov=mongodb --cov-report=term-missing --cov-report=html

# Lint code
lint:
	@echo "Running code linting..."
	uv run ruff check .

# Format code
format:
	@echo "Formatting code..."
	uv run ruff format .

# Run all checks
check: lint format test
	@echo "All checks completed!"

# Clean up temporary files
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/