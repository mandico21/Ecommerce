include .env
export

# enumeration of * .py files storage or folders is required.
files_to_fmt 	?= app
files_to_check 	?= app


## Default target
.DEFAULT_GOAL := run

## Build api docker containers
docker_up:
	docker-compose up --build -d

## Run development server with reload
run:
	uvicorn app.main:create_app --factory --host $(API__HOST) --reload --port $(API__PORT) --log-config logging_config.json

## Run development server with reload (alternative via Python script)
run-dev:
	uv run python run.py

## Run production server with multiple workers
run-prod:
	uvicorn app.main:create_app --factory --host $(API__HOST) --port $(API__PORT) --workers $(API__WORKERS) --no-access-log --log-config logging_config.json

## Format all
fmt: format
format: remove_imports isort black docformatter add-trailing-comma


## Check code quality
chk: check
lint: check
check: flake8 black_check docformatter_check safety bandit

## Migrate database
migrate:
	uv run python -m scripts.migrate

## Rollback migrations in database
migrate-rollback:
	uv run python -m scripts.migrate --rollback

migrate-reload:
	uv run python -m scripts.migrate --reload

## List migrations
migrate-list:
	uv run python -m scripts.migrate --list

## Remove unused imports
remove_imports:
	autoflake -ir --remove-unused-variables \
		--ignore-init-module-imports \
		--remove-all-unused-imports \
		${files_to_fmt}


## Sort imports
isort:
	isort ${files_to_fmt}


## Format code
black:
	black ${files_to_fmt}


## Check code formatting
black_check:
	black --check ${files_to_check}


## Format docstring PEP 257
docformatter:
	docformatter -ir ${files_to_fmt}


## Check docstring formatting
docformatter_check:
	docformatter -cr ${files_to_check}


## Check pep8
flake8:
	flake8 ${files_to_check}

## Check google spec.
pylint:
	pylint ${files_to_check}

## Check pep8
ruff:
	ruff check ${files_to_check}

## Check typing
mypy:
	mypy ${files_to_check}


## Check if all dependencies are secure and do not have any known vulnerabilities
safety:
	safety check --full-report


## Check code security
bandit:
	bandit -r ${files_to_check} -x tests

## ═══════════════════════════════════════════════════════════════════════════════
## Testing
## ═══════════════════════════════════════════════════════════════════════════════

## Run all tests
test:
	pytest

## Run unit tests only
test-unit:
	pytest -m unit

## Run integration tests only
test-integration:
	pytest -m integration

## Run tests with coverage report
test-cov:
	pytest --cov=app --cov-report=term-missing --cov-report=html

## Run tests in verbose mode
test-v:
	pytest -vvv

## Run specific test file
# Usage: make test-file FILE=tests/unit/test_models.py
test-file:
	pytest $(FILE) -v

## Run tests matching pattern
# Usage: make test-k PATTERN="test_create"
test-k:
	pytest -k "$(PATTERN)" -v

## Run tests and stop on first failure
test-x:
	pytest -x

## Run failed tests from last run
test-lf:
	pytest --lf

## ═══════════════════════════════════════════════════════════════════════════════

## Add trailing comma works only on unix.
# an error is expected on windows.
add-trailing-comma:
	find app tests -name "*.py" -exec add-trailing-comma '{}' --py36-plus \;

## Install dependencies
install:
	uv sync

## Clean pycache
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

## Help
help:
	@echo "Available targets:"
	@echo ""
	@echo "  === Server ==="
	@echo "  run           - Run development server with reload"
	@echo "  run-prod      - Run production server with workers"
	@echo ""
	@echo "  === Testing ==="
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-cov      - Run tests with coverage report"
	@echo "  test-v        - Run tests in verbose mode"
	@echo "  test-x        - Run tests, stop on first failure"
	@echo "  test-lf       - Run failed tests from last run"
	@echo ""
	@echo "  === Code Quality ==="
	@echo "  fmt           - Format code"
	@echo "  check         - Run all checks"
	@echo ""
	@echo "  === Database ==="
	@echo "  migrate       - Apply migrations"
	@echo "  migrate-rollback - Rollback migrations"
	@echo "  migrate-list  - List migrations status"
	@echo ""
	@echo "  === Other ==="
	@echo "  install       - Install dependencies"
	@echo "  clean         - Clean pycache"

