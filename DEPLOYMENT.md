# Deployment Guide: Sentinel Growth Microservice

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- Terraform installed (>= 1.0)
- Docker installed (for local testing)

## 1. Secret Manager Setup

Before deploying with Terraform, you must create the required secret in Google Secret Manager.

### Create the Secret

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"
gcloud config set project $PROJECT_ID

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Create the secret (replace YOUR_ACTUAL_API_KEY with your Gemini API key)
echo -n "YOUR_ACTUAL_API_KEY" | gcloud secrets create google-api-key \
    --data-file=- \
    --replication-policy="user-managed" \
    --locations="europe-west2"
```

### Verify the Secret

```bash
# List secrets to confirm creation
gcloud secrets list

# Verify the secret exists (won't show the value)
gcloud secrets describe google-api-key
```

## 2. Font Assets

Add your custom font files to the `assets/fonts/` directory:

```bash
# Example: Copy your fonts
cp /path/to/your/fonts/*.ttf assets/fonts/

# Verify fonts are in place
ls -la assets/fonts/
```

**Note:** The Dockerfile will copy these fonts to `/usr/share/fonts/truetype/custom` in the container.

## 3. Terraform Deployment

### Initialize Terraform

```bash
cd terraform

# Initialize Terraform (downloads providers)
terraform init
```

### Configure Variables

Create a `terraform.tfvars` file:

```hcl
project_id  = "your-gcp-project-id"
region      = "europe-west2"
service_name = "sentinel-growth"
bucket_name = "your-unique-bucket-name"  # Must be globally unique
```

### Plan and Apply

```bash
# Preview changes
terraform plan

# Apply infrastructure
terraform apply
```

**Expected Resources:**
- Service Account (`sentinel-growth-sa`)
- Artifact Registry repository
- GCS bucket with versioning and lifecycle rules
- Cloud Run service (with placeholder image initially)
- IAM bindings for storage, token creation, Vertex AI, and Secret Manager

## 4. Build and Push Docker Image

### Enable Required APIs

```bash
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    aiplatform.googleapis.com
```

### Build the Container

```bash
# Navigate to project root
cd ..

# Set variables
export PROJECT_ID="your-gcp-project-id"
export REGION="europe-west2"
export IMAGE_NAME="sentinel-growth"
export TAG="latest"

# Build the image
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinel-repo/${IMAGE_NAME}:${TAG} .
```

### Authenticate and Push

```bash
# Configure Docker to use gcloud for authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Push the image
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinel-repo/${IMAGE_NAME}:${TAG}
```

## 5. Update Cloud Run Service

Update the Terraform configuration or manually update the service to use your built image:

```bash
gcloud run services update sentinel-growth \
    --region=europe-west2 \
    --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/sentinel-repo/${IMAGE_NAME}:${TAG}
```

**Alternative:** Update `terraform/main.tf` line 105 with your image URL and run `terraform apply`.

## 6. Test the Deployment

### Get the Service URL

```bash
gcloud run services describe sentinel-growth \
    --region=europe-west2 \
    --format='value(status.url)'
```

### Health Check

```bash
curl https://YOUR_SERVICE_URL/health
```

Expected response:
```json
{"status": "ok"}
```

### Test Document Generation

```bash
curl -X POST https://YOUR_SERVICE_URL/generate/proposal \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client-001",
    "domain_profile": "consulting",
    "project_scope": ["Digital Transformation", "Cloud Migration"],
    "financial_data": {"budget": "500000", "duration": "12 months"},
    "template_version": "v1",
    "output_format": "pdf"
  }'
```

Expected response:
```json
{
  "status": "success",
  "url": "https://storage.googleapis.com/..."
}
```

## 7. Monitoring and Logs

### View Logs

```bash
# Stream logs
gcloud run services logs tail sentinel-growth --region=europe-west2

# View in Cloud Console
gcloud run services logs read sentinel-growth --region=europe-west2 --limit=50
```

### Check Metrics

```bash
# Open Cloud Console metrics
gcloud run services list --platform=managed --region=europe-west2
```

## Security Checklist

- ✅ Region locked to `europe-west2`
- ✅ Ingress restricted to `internal-and-cloud-load-balancing`
- ✅ Secrets managed via Secret Manager (not in code or env files)
- ✅ GCS bucket has public access prevention enabled
- ✅ Service account follows least privilege principle
- ✅ Audit logs retained for 365 days

## Troubleshooting

### Secret Not Found Error

```bash
# Verify secret exists
gcloud secrets describe google-api-key

# Check IAM permissions
gcloud secrets get-iam-policy google-api-key
```

### Font Rendering Issues

```bash
# SSH into a running container (for debugging)
gcloud run services proxy sentinel-growth --region=europe-west2

# List available fonts
fc-list
```

### Build Failures

- Ensure `assets/fonts/` directory exists and contains font files
- Check Docker build logs for missing dependencies
- Verify all requirements are pinned in `requirements.txt`

## Cleanup

To destroy all infrastructure:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete the GCS bucket and all documents. Ensure you have backups if needed.
