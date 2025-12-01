import datetime
import structlog
from google.cloud import storage
from src.core.config import settings

logger = structlog.get_logger()

class StorageService:
    def __init__(self):
        try:
            # If credentials are not explicitly set in env, it will try to find default credentials
            self.client = storage.Client()
            self.bucket_name = settings.GCS_BUCKET_NAME
            logger.info("StorageService initialized", bucket=self.bucket_name)
        except Exception as e:
            logger.error("Failed to initialize StorageService", error=str(e))
            self.client = None

    def upload_and_sign(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """
        Uploads a file to GCS and returns a V4 signed URL valid for 15 minutes.
        """
        if not self.client:
            raise RuntimeError("StorageService is not initialized properly")

        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(filename)
            
            # Upload file
            logger.info("Uploading file", filename=filename, content_type=content_type)
            blob.upload_from_string(file_bytes, content_type=content_type)
            
            # Generate Signed URL
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="GET",
            )
            
            return url
        except Exception as e:
            logger.error("Failed to upload and sign file", filename=filename, error=str(e))
            raise e

storage_service = StorageService()
