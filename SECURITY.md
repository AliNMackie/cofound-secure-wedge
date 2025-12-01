# Security Guidelines

## Secret Management

### Current State
The Terraform configuration in `terraform/main.tf` currently uses a placeholder for the `GOOGLE_API_KEY` environment variable:

```hcl
env {
    name = "GOOGLE_API_KEY"
    value = "placeholder_needs_secret_manager"
}
```

### Recommended Approach: Google Secret Manager

**Why Secret Manager?**
- Prevents secrets from being exposed in Terraform state files
- Enables secret rotation without code changes
- Provides audit logging for secret access
- Follows Google Cloud security best practices

**Implementation Steps:**

1. **Create a secret in Secret Manager:**
   ```bash
   echo -n "your-api-key-value" | gcloud secrets create google-api-key \
       --data-file=- \
       --replication-policy="user-managed" \
       --locations="europe-west2"
   ```

2. **Grant the service account access:**
   ```bash
   gcloud secrets add-iam-policy-binding google-api-key \
       --member="serviceAccount:sentinel-growth-sa@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

3. **Update Terraform to reference the secret:**
   ```hcl
   # Add to main.tf
   data "google_secret_manager_secret_version" "api_key" {
     secret = "google-api-key"
     version = "latest"
   }

   # In the Cloud Run service container env block:
   env {
     name = "GOOGLE_API_KEY"
     value = data.google_secret_manager_secret_version.api_key.secret_data
   }
   ```

## Container Security

### ✅ Implemented
- `.env` file is **not** copied into Docker images (removed in audit fix)
- Secrets are injected at runtime via Cloud Run environment variables
- Base image uses `python:3.11-slim` to minimize attack surface

### Best Practices
- Always inject secrets via environment variables at runtime
- Never commit `.env` files to version control (enforced by `.gitignore`)
- Use minimal base images
- Regularly update dependencies to patch vulnerabilities

## Infrastructure Security

### ✅ Configured
- **Region Lock:** All resources deployed to `europe-west2` (data sovereignty)
- **Ingress Control:** Cloud Run service restricted to `internal-and-cloud-load-balancing`
- **Storage Security:** GCS bucket has `public_access_prevention = "enforced"`
- **Audit Logging:** Log retention set to 365 days

## Dependency Security

Run regular security audits:
```bash
pip install safety
safety check -r requirements.txt
```

## Reporting Security Issues

If you discover a security vulnerability, please email [security contact] instead of using the issue tracker.
