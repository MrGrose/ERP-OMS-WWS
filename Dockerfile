FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app --create-home app
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/
COPY pyproject.toml README.md ./
COPY src ./src
RUN uv sync --no-dev
RUN chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "erp_oms_wms.main:app", "--host", "0.0.0.0", "--port", "8000"]

