import structlog
from fastapi import FastAPI
from src.core.config import settings
from src.core.logging import configure_logging
from src.api.routes import router

# Ensure logging is configured before app startup
configure_logging()

app = FastAPI(title=settings.APP_NAME)

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
