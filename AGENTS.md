# Repository Guidelines

## Project Structure & Module Organization
The Python package lives under `src/services`, with domain-specific modules in `mongodb/` and `minio/`. Shared fixtures and integration helpers belong in `integration_tests/`. Unit tests mirror the service layout under `tests/minio` and `tests/mongodb`, and `pyproject.toml` configures `src` as the import root. Use `tests/` for isolated behavior checks and reserve `integration_tests/` for cross-service flows that may touch MinIO or MongoDB mocks.

## Build, Test, and Development Commands
Run `make install` to sync dependencies via `uv`. `make test` executes the default pytest suite with fail-fast enabled, while `make test-verbose` is useful when investigating flaky cases. Use `make test-mongodb` for MongoDB-focused suites and `make test-coverage` to generate coverage metrics (`htmlcov/`). For static analysis, `make lint` runs `ruff check .`, `make format` applies `ruff format .`, and `make check` chains lint, format, and unit tests.

## Coding Style & Naming Conventions
This project targets Python 3.10+. Keep modules and packages named in snake_case, with PascalCase for classes and snake_case for functions and variables. Ruff is configured with `lint.select = ["ALL"]`, so favor explicit imports, type hints, and small functions to satisfy strict rules. Format code using `make format` before committing; do not hand-edit Ruff-suppressed sections.

## Testing Guidelines
Write tests with pytest and place async scenarios alongside the feature they cover. Name test files `test_*.py` and prefer descriptive test function names (`test_minio_client_handles_missing_bucket`). When adding new behavior, extend existing fixtures or create local ones under `tests/conftest.py` as needed. Generate coverage locally with `make test-coverage` and ensure new code maintains or improves module coverage, especially for storage adapters.

## Commit & Pull Request Guidelines
Follow the existing Git history: start commit subjects with an action verb in present tense (`Add`, `Fix`, `Refactor`) and keep them under ~60 characters. Group related changes together and include brief body details when context is non-obvious. Pull requests should link the motivating issue, summarize behavior changes, call out configuration updates, and include screenshots or logs if they affect deployment or data pipelines.
