terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------------------
# Service Accounts
# ------------------------------------------------------------------------------

# Create a Service Account for Cloud Functions if one isn't provided externally.
# In a real scenario, we might import this or manage it here.
# We will create one to be explicit and secure.
resource "google_service_account" "cloud_function_sa" {
  account_id   = "ir35-cloud-function-sa"
  display_name = "Cloud Function Service Account"
  description  = "Service Account for IR35 Platform Cloud Functions"
}

# ------------------------------------------------------------------------------
# Secret Manager Resources
# ------------------------------------------------------------------------------

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
  }
}

resource "google_secret_manager_secret" "n8n_webhook_secret" {
  secret_id = "n8n-webhook-secret"

  replication {
    auto {}
  }

  labels = {
    environment = var.environment
  }
}

# ------------------------------------------------------------------------------
# IAM Bindings
# ------------------------------------------------------------------------------

# Allow the Cloud Function Service Account to access the Gemini API Key
resource "google_secret_manager_secret_iam_member" "gemini_api_key_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Allow the Cloud Function Service Account to access the n8n Webhook Secret
resource "google_secret_manager_secret_iam_member" "n8n_webhook_secret_access" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.n8n_webhook_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}
