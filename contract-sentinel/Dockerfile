# Syntax to allow using ARG in FROM
ARG SERVICE_NAME=api

FROM python:3.11-slim as base
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# This line was already fixed and is working:
COPY contract-sentinel/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# --- FIX START ---
# We changed the source path from "shared" to "contract-sentinel/shared"
COPY contract-sentinel/shared /app/shared
# --- FIX END ---

FROM base as api
COPY contract-sentinel/apps/api /app/apps/api
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

FROM base as worker
COPY contract-sentinel/apps/worker /app/apps/worker
CMD ["python", "-m", "apps.worker.main"]

FROM ${SERVICE_NAME} as final
