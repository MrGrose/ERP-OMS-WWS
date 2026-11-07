.PHONY: dev test lint worker migrate

dev:
	uv run uvicorn erp_oms_wms.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check . && uv run mypy src

migrate:
	uv run alembic upgrade head

worker:
	uv run arq erp_oms_wms.worker.WorkerSettings

