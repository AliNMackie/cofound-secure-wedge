import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_ID: str = os.getenv("PROJECT_ID", "default-project")
    SUBSCRIPTION_ID: str = os.getenv("SUBSCRIPTION_ID", "worker-sub")
    # Using the topic name from previous steps as default, though worker uses subscription
    TOPIC_ID: str = os.getenv("TOPIC_ID", "contract-ingestion-queue") 
    LOCATION: str = os.getenv("LOCATION", "us-central1")

settings = Settings()
