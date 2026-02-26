.PHONY: help install test test-verbose test-coverage test-models test-repos test-handlers test-exceptions clean lint format type-check

help:
	@echo "Multi-Player Backend Test Suite"
	@echo "================================"
	@echo ""
	@echo "Available commands:"
	@echo "  make install          - Install test dependencies"
	@echo "  make test             - Run all tests"
	@echo "  make test-verbose     - Run tests with verbose output"
	@echo "  make test-coverage    - Run tests with coverage report"
	@echo "  make test-models      - Run model tests only"
	@echo "  make test-repos       - Run repository tests only"
	@echo "  make test-handlers    - Run handler tests only"
	@echo "  make test-exceptions  - Run exception tests only"
	@echo "  make clean            - Remove test artifacts"
	@echo "  make lint             - Run code quality checks"
	@echo "  make format           - Format code with black"
	@echo "  make type-check       - Run type checking with mypy"
	@echo ""

install:
	pip install -r requirements.txt

test:
	pytest unit -q

test-verbose:
	pytest unit -v

test-coverage:
	pytest unit --cov=../src/layers/common/python --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

test-models:
	pytest unit/test_models.py -v

test-repos:
	pytest unit/test_repositories.py -v

test-handlers:
	pytest unit/test_lambda_handlers.py -v

test-exceptions:
	pytest unit/test_exceptions_and_responses.py -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache

lint:
	flake8 unit/ conftest.py
	black --check unit/ conftest.py
	isort --check-only unit/ conftest.py

format:
	black unit/ conftest.py
	isort unit/ conftest.py

type-check:
	mypy unit/ conftest.py --ignore-missing-imports

all: clean install test-coverage lint
