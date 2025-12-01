# IR35 Assessment Tool

## Overview
The IR35 Assessment Tool is a cloud-native application designed to assist in determining the IR35 status of contractors. It leverages Google Cloud Platform (GCP) services, including Vertex AI for RAG (Retrieval-Augmented Generation) and Gemini Pro for intelligent assessments.

## Architecture
The system is built using a serverless architecture on GCP:

*   **Backend**:
    *   `assessment_api`: A Cloud Function (Python) that handles assessment requests. It queries the Vector Search index for relevant case law and uses Gemini 1.5 Pro to generate a determination.
    *   `rag_indexer`: A Cloud Function (Python) that processes PDF documents, chunks them, generates embeddings, and updates the Vertex AI Vector Search index.
*   **Data Storage**:
    *   **Firestore**: Stores assessment requests, responses, and audit logs.
    *   **Cloud Storage**: Stores source PDF documents for indexing.
    *   **Vertex AI Vector Search**: Stores embeddings for efficient retrieval of context.
*   **Infrastructure**: Managed via Terraform.

## Prerequisites
*   Google Cloud Platform Account
*   Terraform installed
*   Python 3.11+
*   Google Cloud SDK (`gcloud`)

## Setup & Deployment

### 1. Environment Setup
Ensure you have authenticated with GCP:
```bash
gcloud auth application-default login
```

### 2. Infrastructure Deployment (Terraform)
Navigate to the `terraform/` directory and apply the configuration:
```bash
cd terraform
terraform init
terraform apply
```
This will provision all necessary resources, including Cloud Functions, Firestore, and Vertex AI components.

## Usage

### Assessment API
Send a POST request to the `assessment-api` Cloud Function URL (output from Terraform):

```json
POST /assess_engagement
{
  "role_details": "Senior Python Developer working on backend API...",
  "contract_type": "T&M",
  "answers": {
    "substitution": "Right to substitute exists...",
    "control": "Client determines working hours..."
  },
  "engagement_id": "eng-123"
}
```

### Indexing Documents
Trigger the `rag-indexer` function with a Cloud Storage URL to a PDF:

```json
POST /index_documents
{
  "document_url": "gs://your-data-bucket/case-law.pdf"
}
```

## Development
*   **Backend**: Located in `backend/`. Each function has its own `requirements.txt`.
*   **Terraform**: Located in `terraform/`.

## License
[License Name]
