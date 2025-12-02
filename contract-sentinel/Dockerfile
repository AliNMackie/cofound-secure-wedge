# Syntax to allow using ARG in FROM
ARG SERVICE_NAME=api

FROM python:3.11-slim as base
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# --- FIX START ---
# Because context is now ROOT, we must specify the folder path
COPY contract-sentinel/requirements.txt .
# --- FIX END ---

RUN pip install --no-cache-dir -r requirements.txt

# Now we can copy shared because context is root
COPY shared /app/shared

FROM base as api
# --- FIX START ---
# Update path to include contract-sentinel folder
COPY contract-sentinel/apps/api /app/apps/api
# --- FIX END ---
CMD ["sh", "-c", "uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

FROM base as worker
# --- FIX START ---
# Update path to include contract-sentinel folder
COPY contract-sentinel/apps/worker /app/apps/worker
# --- FIX END ---
CMD ["python", "-m", "apps.worker.main"]

FROM ${SERVICE_NAME} as final