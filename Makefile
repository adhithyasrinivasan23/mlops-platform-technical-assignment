.PHONY: build up down test-backend test-frontend test-e2e test-all lint clean

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down -v

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run test

test-e2e:
	cd frontend && npx playwright test

lint:
	cd backend && flake8 .
	cd frontend && npx prettier --check "src/**/*.ts"

test-all: test-backend test-frontend test-e2e
