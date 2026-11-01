.PHONY: help install-backend install-frontend generate-starter generate-full test run-backend run-frontend docker-up docker-down

help:
	@echo "StockMind AI — Unified Inventory Intelligence Commands"
	@echo "---------------------------------------------------------"
	@echo "make install-backend    : Install Python requirements"
	@echo "make install-frontend   : Install npm frontend packages"
	@echo "make generate-starter   : Generate starter dataset (100 SKUs, 1k movements)"
	@echo "make generate-full      : Generate full dataset (5k SKUs, 1M movements)"
	@echo "make test               : Run pytest automated test suite"
	@echo "make run-backend        : Start FastAPI backend server"
	@echo "make run-frontend       : Start Vite frontend development server"
	@echo "make docker-up          : Start PostgreSQL and backend with Docker Compose"
	@echo "make docker-down        : Stop containers"

install-backend:
	pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

generate-starter:
	python -m data_engine.run_pipeline --profile starter --seed 20261022

generate-full:
	python -m data_engine.run_pipeline --profile full --seed 20261022

test:
	pytest -v backend/tests

run-backend:
	uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

run-frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up -d

docker-down:
	docker compose down
