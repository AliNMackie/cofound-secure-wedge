terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- Secret Manager ---
# Reference to the Google API Key secret (must be created manually or via separate process)
data "google_secret_manager_secret_version" "google_api_key" {
  secret  = "google-api-key"
  version = "latest"
}

# --- Service Account ---
resource "google_service_account" "sentinel_sa" {
  account_id   = "sentinel-growth-sa"
  display_name = "Service Account for Sentinel Growth Service"
}

# --- Artifact Registry ---
resource "google_artifact_registry_repository" "sentinel_repo" {
  location      = var.region
  repository_id = "sentinel-repo"
  description   = "Docker repository for Sentinel Growth"
  format        = "DOCKER"
}

# --- Storage Bucket (Document Vault) ---
resource "google_storage_bucket" "vault" {
  name                        = var.bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false # Safety: Do not delete if not empty

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }
}

# --- IAM Bindings ---
# Grant SA permission to create objects in the specific bucket
resource "google_storage_bucket_iam_member" "sa_storage_creator" {
  bucket = google_storage_bucket.vault.name
  role   = "roles/storage.objectCreator"
  member = "serviceAccount:${google_service_account.sentinel_sa.email}"
}

# Grant SA permission to sign blobs (Required for V4 Signed URLs)
resource "google_project_iam_member" "sa_token_creator" {
  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = "serviceAccount:${google_service_account.sentinel_sa.email}"
}

# Grant SA permission to use Vertex AI (Gemini)
resource "google_project_iam_member" "sa_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.sentinel_sa.email}"
}

# Grant SA permission to access secrets from Secret Manager
resource "google_project_iam_member" "sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.sentinel_sa.email}"
}

# --- Cloud Run Service ---
resource "google_cloud_run_service" "default" {
  name     = var.service_name
  location = var.region

  metadata {
    annotations = {
      "run.googleapis.com/ingress" = "internal-and-cloud-load-balancing"
    }
  }

  template {
    spec {
      service_account_name = google_service_account.sentinel_sa.email
      containers {
        # Using a placeholder image for initial deployment definition.
        # In a real pipeline, this would be updated to the built image.
        image = "us-docker.pkg.dev/cloudrun/container/hello" 
        
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.vault.name
        }
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
            name  = "GOOGLE_API_KEY"
            value = data.google_secret_manager_secret_version.google_api_key.secret_data
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
  
  autogenerate_revision_name = true
}

# --- Audit Logs ---
# Configure Retention for Default Logs Bucket to 365 days (1 year)
resource "google_logging_project_bucket_config" "default_log_bucket" {
    project        = var.project_id
    location       = "global" # _Default bucket is global
    bucket_id      = "_Default"
    retention_days = 365
}
