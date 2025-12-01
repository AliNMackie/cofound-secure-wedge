# Sentinel Growth Microservice

[![Cloud Run](https://img.shields.io/badge/Cloud%20Run-Ready-blue)](https://cloud.google.com/run)
[![Region](https://img.shields.io/badge/Region-europe--west2-green)](https://cloud.google.com/regions)
[![Security](https://img.shields.io/badge/Security-Secret%20Manager-orange)](SECURITY.md)

AI-powered document generation microservice for creating professional proposals in PDF and DOCX formats using Google Gemini and WeasyPrint.

## 🚀 Features

- **AI Content Generation** - Leverages Google Gemini 1.5 Flash for intelligent content creation
- **Multi-Format Export** - Generate documents as PDF or DOCX
- **Domain-Specific Profiles** - Tailored tone and content for consulting, tech, and finance sectors
- **Secure Storage** - Automated upload to Google Cloud Storage with time-limited signed URLs
- **JSON Logging** - Structured logs via `structlog` for Cloud Logging integration
- **Production-Ready** - Region-locked, secret management, and audit compliance

## 📋 Architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Client    │─────▶│   Cloud Run      │─────▶│   Gemini    │
│  (API Call) │      │  (FastAPI)       │      │  (AI Gen)   │
└─────────────┘      └──────────────────┘      └─────────────┘
                              │
                              ├─────▶ WeasyPrint (PDF)
                              ├─────▶ DocXTPL (DOCX)
                              └─────▶ GCS (Storage)
```

## 🛡️ Security & Compliance

- **Region Lock:** All resources deployed to `europe-west2` (UK)
- **Secrets:** Managed via Google Secret Manager (no hardcoded keys)
- **Ingress:** Restricted to `internal-and-cloud-load-balancing`
- **Storage:** Public access prevention enforced on GCS buckets
- **Audit Logs:** 365-day retention

See [SECURITY.md](SECURITY.md) for detailed security guidelines.

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI + Uvicorn |
| **AI Engine** | Google Gemini 1.5 Flash |
| **PDF Rendering** | WeasyPrint |
| **DOCX Rendering** | python-docx-template |
| **Storage** | Google Cloud Storage |
| **Logging** | structlog (JSON) |
| **Infrastructure** | Terraform + Cloud Run |

## 🚀 Quick Start

### Local Development

1. **Clone and Install Dependencies**
   ```bash
   git clone <repository-url>
   cd sentinel-growth
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your GOOGLE_API_KEY
   ```

3. **Add Font Assets**
   ```bash
   # Place your .ttf or .otf fonts in assets/fonts/
   cp /path/to/fonts/*.ttf assets/fonts/
   ```

4. **Run Locally**
   ```bash
   uvicorn src.main:app --reload --port 8080
   ```

5. **Test the API**
   ```bash
   curl http://localhost:8080/health
   ```

### Cloud Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

**Quick Deploy:**
```bash
# 1. Create secret
echo -n "YOUR_API_KEY" | gcloud secrets create google-api-key --data-file=-

# 2. Deploy infrastructure
cd terraform
terraform init
terraform apply

# 3. Build and push
docker build -t europe-west2-docker.pkg.dev/PROJECT_ID/sentinel-repo/sentinel-growth:latest .
docker push europe-west2-docker.pkg.dev/PROJECT_ID/sentinel-repo/sentinel-growth:latest

# 4. Update Cloud Run
gcloud run services update sentinel-growth --image=...
```

## 📡 API Reference

### Health Check
```http
GET /health
```

**Response:**
```json
{"status": "ok"}
```

### Generate Proposal
```http
POST /generate/proposal
Content-Type: application/json
```

**Request Body:**
```json
{
  "client_id": "acme-corp-001",
  "domain_profile": "consulting",
  "project_scope": [
    "Digital Transformation",
    "Cloud Migration"
  ],
  "financial_data": {
    "budget": "500000",
    "duration": "12 months"
  },
  "template_version": "v1",
  "output_format": "pdf"
}
```

**Response:**
```json
{
  "status": "success",
  "url": "https://storage.googleapis.com/sentinel-growth-artifacts/proposal_acme-corp-001_abc123.pdf?X-Goog-Signature=..."
}
```

**Domain Profiles:**
- `consulting` - Professional, authoritative, data-driven
- `tech` - Technical, precise, innovative
- `finance` - Formal, conservative, risk-aware

**Output Formats:**
- `pdf` - Generated via WeasyPrint
- `docx` - Generated via python-docx-template

## 🏗️ Project Structure

```
sentinel-growth/
├── src/
│   ├── main.py              # FastAPI application entry
│   ├── api/
│   │   └── routes.py        # API endpoints
│   ├── core/
│   │   ├── config.py        # Configuration management
│   │   └── logging.py       # Structured logging setup
│   ├── schemas/
│   │   ├── requests.py      # Pydantic request models
│   │   └── responses.py     # Pydantic response models
│   ├── services/
│   │   ├── content.py       # Gemini content generation
│   │   ├── pdf_factory.py   # PDF rendering
│   │   ├── word_factory.py  # DOCX rendering
│   │   └── storage.py       # GCS operations
│   └── templates/           # Document templates
├── assets/
│   └── fonts/               # Custom fonts for PDF rendering
├── terraform/
│   ├── main.tf              # Infrastructure as Code
│   ├── variables.tf         # Terraform variables
│   └── outputs.tf           # Terraform outputs
├── Dockerfile               # Container image definition
├── requirements.txt         # Python dependencies
├── DEPLOYMENT.md            # Deployment guide
├── SECURITY.md              # Security documentation
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Gemini API key (from Secret Manager) | - |
| `GCS_BUCKET_NAME` | Storage bucket name | `sentinel-growth-artifacts` |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | - |
| `PORT` | Server port | `8080` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Terraform Variables

See `terraform/variables.tf`:
- `project_id` - GCP project ID
- `region` - Deployment region (default: `europe-west2`)
- `service_name` - Cloud Run service name
- `bucket_name` - GCS bucket name

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Test API locally
curl -X POST http://localhost:8080/generate/proposal \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## 📊 Monitoring

### View Logs
```bash
gcloud run services logs tail sentinel-growth --region=europe-west2
```

### Metrics
- Cloud Run metrics available in GCP Console
- Structured JSON logs in Cloud Logging
- Storage access logs via GCS audit logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

[Add your license here]

## 🆘 Support

For issues and questions:
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment troubleshooting
- Review [SECURITY.md](SECURITY.md) for security concerns
- Open an issue in the repository

## 🔗 Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [WeasyPrint Documentation](https://doc.courtbouillon.org/weasyprint/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
