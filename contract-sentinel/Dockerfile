# Syntax to allow using ARG in FROM
ARG SERVICE_NAME=api

FROM python:3.11-slim as base
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared

FROM base as api
COPY apps/api /app/apps/api
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

FROM base as worker
COPY apps/worker /app/apps/worker
CMD ["python", "-m", "apps.worker.main"]

FROM ${SERVICE_NAME} as final
