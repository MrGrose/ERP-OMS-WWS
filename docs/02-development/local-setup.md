# Local setup

## Docker Compose (рекомендуется)

```bash
cp .env.example .env
docker compose up -d postgres redis
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erp-oms-wms
uv sync
make migrate
make dev
```

Сервисы: `app` (порт 8000), `postgres` (5432), `redis` (6379), `worker` (ARQ).
Перед первым запуском API примените миграции: `make migrate`.

## Полный стек (app + worker в Compose)

```bash
docker compose up --build
```

После старта `postgres` один раз с хоста:

```bash
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erp-oms-wms
make migrate   # или: uv run alembic upgrade head
```

Миграции в образ **не** встроены намеренно — перед демо нужен явный `alembic upgrade head`.

В `compose.yml` у `worker` заданы `DATABASE_URL` и Redis; без БД фоновые задачи не работают.

## PostgreSQL (только БД)

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:16
```

Скопируй `.env.postgres.example` → `.env`.

## Arq worker (на хосте)

На хосте Redis по умолчанию `localhost`. В Compose задаётся `REDIS_HOST=redis`.

```bash
export DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/erp-oms-wms
make worker
# или: uv run arq erp_oms_wms.worker.WorkerSettings
```

## Redis

Если выбран Docker, Redis — сервис `redis` в `compose.yml`. Отдельный `compose.redis.yml` в репозитории не используется.

## Локальный запуск (без Docker)

```bash
uv sync
uv run pre-commit install
uv run pytest
```

API:

```bash
uv run uvicorn erp_oms_wms.main:app --reload
```
