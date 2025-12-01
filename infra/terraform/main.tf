variable "project_id" {
  description = "The ID of the Google Cloud project"
  type        = string
}

variable "region" {
  description = "The region to deploy resources"
  type        = string
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Google Cloud Storage bucket
resource "google_storage_bucket" "contract_uploads" {
  name          = "contract-uploads-raw-${var.project_id}"
  location      = var.region
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 3
    }
    action {
      type = "Delete"
    }
  }
}

# Firestore Database (Native mode)
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Pub/Sub Topic
resource "google_pubsub_topic" "contract_ingestion_queue" {
  name = "contract-ingestion-queue"
}

# Pub/Sub Subscription
resource "google_pubsub_subscription" "worker_sub" {
  name  = "worker-sub"
  topic = google_pubsub_topic.contract_ingestion_queue.name
}

# Service Accounts
resource "google_service_account" "sa_api" {
  account_id   = "sa-api"
  display_name = "Contract API Service Account"
}

resource "google_service_account" "sa_worker" {
  account_id   = "sa-worker"
  display_name = "Contract Worker Service Account"
}

# IAM Roles for sa-api
resource "google_project_iam_member" "sa_api_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.sa_api.email}"
}

# IAM Roles for sa-worker
resource "google_project_iam_member" "sa_worker_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.sa_worker.email}"
}

resource "google_project_iam_member" "sa_worker_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.sa_worker.email}"
}

resource "google_project_iam_member" "sa_worker_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.sa_worker.email}"
}

resource "google_project_iam_member" "sa_worker_dlp_user" {
  project = var.project_id
  role    = "roles/dlp.user"
  member  = "serviceAccount:${google_service_account.sa_worker.email}"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "contract_api" {
  name     = "contract-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.sa_api.email
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder image
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "noauth" {
  project  = google_cloud_run_v2_service.contract_api.project
  location = google_cloud_run_v2_service.contract_api.location
  name     = google_cloud_run_v2_service.contract_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Cloud Run Job
resource "google_cloud_run_v2_job" "contract_worker" {
  name     = "contract-worker"
  location = var.region

  template {
    template {
      service_account = google_service_account.sa_worker.email
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello" # Placeholder image
      }
    }
  }
}
