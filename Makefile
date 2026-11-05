SHELL := /bin/bash

.PHONY: dev-up dev-down api-up backend-check backend-test backend-migrate backend-seed

dev-up:
	docker compose up -d postgres redis

dev-down:
	docker compose down

api-up:
	docker compose --profile app up --build -d

backend-check:
	cd backend && DJANGO_DEBUG=true python manage.py check
	cd backend && DJANGO_DEBUG=true python manage.py makemigrations --check --dry-run

backend-test:
	cd backend && DJANGO_DEBUG=true pytest -q

backend-migrate:
	cd backend && DJANGO_DEBUG=true python manage.py migrate

backend-seed:
	cd backend && DJANGO_DEBUG=true python manage.py seed_catalog
