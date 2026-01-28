.PHONY: help dev prod down logs test lint format migrate migration shell

help:
	@echo "Available commands:"
	@echo "  make dev        - Start development environment"
	@echo "  make prod       - Start production environment"
	@echo "  make down       - Stop all containers"
	@echo "  make logs       - View container logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter"
	@echo "  make format     - Format code"
	@echo "  make migrate    - Run database migrations"
	@echo "  make migration  - Create new migration (usage: make migration m='message')"
	@echo "  make shell      - Open shell in API container"

dev:
	docker compose -f docker-compose.dev.yml up --build

prod:
	docker compose up --build -d

down:
	docker compose down
	docker compose -f docker-compose.dev.yml down

logs:
	docker compose logs -f

test:
	pytest -v --cov=app tests/

lint:
	ruff check app tests

format:
	ruff format app tests
	ruff check --fix app tests

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(m)"

shell:
	docker compose exec api /bin/bash
