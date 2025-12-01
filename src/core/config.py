from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Sentinel-Growth"
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    GOOGLE_API_KEY: str = ""
    GCS_BUCKET_NAME: str = "sentinel-growth-artifacts"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
