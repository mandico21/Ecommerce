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
	uvicorn app.main:create_app --host ${API__HOST:-localhost} --reload --port ${API__PORT:-8000}

## Run production server with multiple workers
run-prod:
	uvicorn app.main:create_app --host ${API__HOST:-0.0.0.0} --port ${API__PORT:-8000} --workers ${API__WORKERS:-4} --no-access-log

## Run with gunicorn (recommended for production)
run-gunicorn:
	gunicorn app.main:create_app --worker-class uvicorn.workers.UvicornWorker --workers ${API__WORKERS:-4} --bind ${API__HOST:-0.0.0.0}:${API__PORT:-8000} --timeout ${API__REQUEST_TIMEOUT:-30} --graceful-timeout ${API__GRACEFUL_SHUTDOWN_TIMEOUT:-30}

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
	@echo "  run          - Run development server with reload"
	@echo "  run-prod     - Run production server with workers"
	@echo "  run-gunicorn - Run with gunicorn (recommended for production)"
	@echo "  fmt          - Format code"
	@echo "  check        - Run all checks"
	@echo "  migrate      - Apply migrations"
	@echo "  install      - Install dependencies"
	@echo "  clean        - Clean pycache"

