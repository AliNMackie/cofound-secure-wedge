# ContractSentinel

ContractSentinel is a SaaS platform for analyzing legal contracts using Generative AI. It features a scalable microservices architecture with a FastAPI gateway and background workers processing contracts via Google Cloud Pub/Sub, Vertex AI, and DLP.

## Architecture

- **API (`apps/api`):** FastAPI application handling file uploads and status queries.
- **Worker (`apps/worker`):** Background worker for PII redaction and Contract Analysis (Gemini 1.5 Pro + Flash Shadow Mode).
- **Shared (`shared`):** Common data models and database utilities.
- **Infrastructure:** Managed via Terraform on Google Cloud (Run, Firestore, Pub/Sub, Storage).

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Google Cloud SDK (`gcloud`)
- Terraform

### Local Development (Docker Compose)

You can run the full stack locally (with Pub/Sub and Firestore emulators):

```bash
docker-compose up --build
```

Then run the integration test:

```bash
python3 -m venv venv
source venv/bin/activate
pip install requests pypdf
python tests/integration_test.py
```

### Deployment to Google Cloud

1. **Authentication:**
   ```bash
   gcloud auth login
   gcloud config set project [YOUR_PROJECT_ID]
   gcloud auth application-default login
   ```

2. **Infrastructure Provisioning:**
   ```bash
   cd infra/terraform
   terraform init
   terraform apply -var="project_id=[YOUR_PROJECT_ID]"
   ```

3. **Build and Deploy:**
   
   Build the images using Cloud Build or locally and push to Artifact Registry (ensure repo exists):
   
   ```bash
   # Build API
   gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/contract-api --build-arg SERVICE_NAME=api .
   
   # Build Worker
   gcloud builds submit --tag gcr.io/[YOUR_PROJECT_ID]/contract-worker --build-arg SERVICE_NAME=worker .
   ```

   Deploy to Cloud Run:

   ```bash
   # Deploy API Service
   gcloud run deploy contract-api \
     --image gcr.io/[YOUR_PROJECT_ID]/contract-api \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --set-env-vars PROJECT_ID=[YOUR_PROJECT_ID],BUCKET_NAME=contract-uploads-raw-[YOUR_PROJECT_ID]

   # Deploy Worker Job
   # Note: Workers are typically deployed as Cloud Run Services (for push subs) or Jobs (for pull subs/tasks).
   # Our Terraform setup created a Cloud Run Job, but our code uses a streaming pull subscriber 
   # which is long-running. For a streaming pull worker, a Cloud Run Service (min instances 1) 
   # or a Compute Engine instance is often better. 
   # If deploying as a Job, it runs to completion, so the code would need to process a batch and exit.
   # Given the `while True` loop in main.py, it's designed as a continuous service.
   
   gcloud run deploy contract-worker-service \
     --image gcr.io/[YOUR_PROJECT_ID]/contract-worker \
     --region us-central1 \
     --no-allow-unauthenticated \
     --set-env-vars PROJECT_ID=[YOUR_PROJECT_ID]
   ```
