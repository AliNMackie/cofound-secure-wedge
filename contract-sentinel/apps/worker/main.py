import json
import logging
import time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from apps.worker.config import settings
from apps.worker.processor import ContractProcessor

import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import os
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def start_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    # Listen on all interfaces
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"Health check server listening on port {port}")
    server.serve_forever()

def main():
    # Start health check in background
    t = threading.Thread(target=start_health_check_server, daemon=True)
    t.start()

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
