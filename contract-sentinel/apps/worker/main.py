import json
import logging
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from apps.worker.config import settings
from apps.worker.processor import ContractProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Worker starting...")
    
    project_id = settings.PROJECT_ID
    subscription_id = settings.SUBSCRIPTION_ID
    
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    
    processor = ContractProcessor()

    def callback(message):
        logger.info(f"Received message: {message.data}")
        try:
            data = json.loads(message.data.decode("utf-8"))
            job_id = data.get("job_id")
            gcs_path = data.get("gcs_path")
            
            if job_id and gcs_path:
                processor.process_job(job_id, gcs_path)
            else:
                logger.warning("Invalid message format")
                
            message.ack()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            message.nack()

    streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
    logger.info(f"Listening for messages on {subscription_path}...")

    # Wrap subscriber in a try/except to handle errors during setup or long running
    with subscriber:
        try:
            # When `timeout` is not set, result() will block indefinitely,
            # unless an exception is encountered first.
            streaming_pull_future.result()
        except TimeoutError:
            streaming_pull_future.cancel()  # Trigger the shutdown.
            streaming_pull_future.result()  # Block until the shutdown is complete.
        except Exception as e:
            logger.error(f"Streaming pull failed: {e}")

if __name__ == "__main__":
    main()
