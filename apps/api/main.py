import json
import uuid
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from google.cloud import storage, pubsub_v1
from shared.database import FirestoreClient
from apps.api.config import settings
from apps.api.dependencies import get_tenant_id

app = FastAPI()

# Initialize clients
# We initialize them here to reuse them, but in a real app might use dependency injection for them too
# or handle them as global singletons
try:
    storage_client = storage.Client(project=settings.PROJECT_ID)
    pubsub_publisher = pubsub_v1.PublisherClient()
    firestore_client = FirestoreClient(project_id=settings.PROJECT_ID)
except Exception as e:
    # Fallback for local testing if credentials aren't present
    print(f"Warning: Cloud clients failed to initialize: {e}")
    storage_client = None
    pubsub_publisher = None
    firestore_client = None

@app.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_contract(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    if not storage_client or not pubsub_publisher or not firestore_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unavailable: Cloud clients not initialized"
        )

    # 1. Upload to GCS
    file_id = str(uuid.uuid4())
    gcs_path = f"uploads/{tenant_id}/{file_id}.pdf"
    
    try:
        bucket = storage_client.bucket(settings.BUCKET_NAME)
        blob = bucket.blob(gcs_path)
        blob.upload_from_file(file.file, content_type="application/pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # 2. Create Job in Firestore
    try:
        # Full GCS URI format: gs://bucket_name/path
        full_gcs_uri = f"gs://{settings.BUCKET_NAME}/{gcs_path}"
        job_id = firestore_client.create_job(tenant_id=tenant_id, file_path=full_gcs_uri)
    except Exception as e:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job record: {str(e)}"
        )

    # 3. Publish to Pub/Sub
    try:
        topic_path = pubsub_publisher.topic_path(settings.PROJECT_ID, settings.TOPIC_ID)
        message_json = json.dumps({
            "job_id": job_id,
            "gcs_path": full_gcs_uri
        }).encode("utf-8")
        
        future = pubsub_publisher.publish(topic_path, data=message_json)
        future.result(timeout=10) # Block until published to ensure reliability
    except Exception as e:
         # Note: If publishing fails, we have an orphan job and file. 
         # Ideally we'd rollback, but for this scope logging/erroring is acceptable.
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue job: {str(e)}"
        )

    return {"job_id": job_id}

@app.get("/job/{job_id}")
async def get_job_status(
    job_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    try:
        doc_ref = firestore_client.client.collection("contract_jobs").document(job_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Job not found")
        
        data = doc.to_dict()
        if data.get("tenant_id") != tenant_id:
             raise HTTPException(status_code=403, detail="Unauthorized to access this job")
             
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
