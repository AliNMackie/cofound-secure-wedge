import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_ID: str = os.getenv("PROJECT_ID", "default-project")
    BUCKET_NAME: str = os.getenv("BUCKET_NAME", "contract-uploads-raw-default")
    TOPIC_ID: str = os.getenv("TOPIC_ID", "contract-ingestion-queue")

settings = Settings()
