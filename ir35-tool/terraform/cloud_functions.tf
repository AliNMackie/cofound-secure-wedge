resource "google_storage_bucket" "function_source_bucket" {
  name                        = "${var.project_id}-function-source"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true
  labels = {
    environment = var.environment
    component   = "rag-indexer"
  }
}

# ------------------------------------------------------------------------------
# RAG Indexer Function
# ------------------------------------------------------------------------------

data "archive_file" "rag_indexer_source" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/rag_indexer"
  output_path = "${path.module}/rag_indexer.zip"
}

resource "google_storage_bucket_object" "rag_indexer_zip" {
  name   = "rag_indexer_${data.archive_file.rag_indexer_source.output_md5}.zip"
  bucket = google_storage_bucket.function_source_bucket.name
  source = data.archive_file.rag_indexer_source.output_path
}

resource "google_cloudfunctions2_function" "rag_indexer" {
  name        = "rag-indexer"
  location    = var.region
  description = "Indexes documents for IR35 RAG system"

  build_config {
    runtime     = "python311"
    entry_point = "index_documents"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source_bucket.name
        object = google_storage_bucket_object.rag_indexer_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 3
    available_memory   = "512M"
    timeout_seconds    = 540
    vpc_connector      = google_vpc_access_connector.connector.id # Added VPC connector

    service_account_email = local.sa_email

    environment_variables = {
      PROJECT_ID           = var.project_id
      REGION               = var.region
      VERTEX_AI_ENDPOINT   = google_vertex_ai_index_endpoint.endpoint.name
      VERTEX_AI_INDEX_NAME = google_vertex_ai_index.index.name
    }
  }

  labels = {
    environment = var.environment
    component   = "rag-indexer"
  }
}

# ------------------------------------------------------------------------------
# Assessment API Function
# ------------------------------------------------------------------------------

data "archive_file" "assessment_api_source" {
  type        = "zip"
  source_dir  = "${path.module}/../backend/assessment_api"
  output_path = "${path.module}/assessment_api.zip"
}

resource "google_storage_bucket_object" "assessment_api_zip" {
  name   = "assessment_api_${data.archive_file.assessment_api_source.output_md5}.zip"
  bucket = google_storage_bucket.function_source_bucket.name
  source = data.archive_file.assessment_api_source.output_path
}

resource "google_cloudfunctions2_function" "assessment_api" {
  name        = "assessment-api"
  location    = var.region
  description = "Assessment API for IR35 determinations"

  build_config {
    runtime     = "python311"
    entry_point = "assess_engagement"
    source {
      storage_source {
        bucket = google_storage_bucket.function_source_bucket.name
        object = google_storage_bucket_object.assessment_api_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 10
    available_memory   = "1024M" # Gemini needs more memory
    timeout_seconds    = 60
    ingress_settings   = "ALLOW_INTERNAL_AND_GCLB"                # API Gateway only
    vpc_connector      = google_vpc_access_connector.connector.id # Added VPC connector

    service_account_email = local.sa_email

    environment_variables = {
      PROJECT_ID           = var.project_id
      REGION               = var.region
      VERTEX_AI_ENDPOINT   = google_vertex_ai_index_endpoint.endpoint.name
      VERTEX_AI_INDEX_NAME = google_vertex_ai_index.index.name
    }
  }

  labels = {
    environment = var.environment
    component   = "assessment-api"
  }
}

# ------------------------------------------------------------------------------
# IAM Bindings for Cloud Function Service Account
# ------------------------------------------------------------------------------

# Allow SA to read/write to the source bucket (build needs read)
resource "google_storage_bucket_iam_member" "sa_source_bucket_access" {
  bucket = google_storage_bucket.function_source_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${local.sa_email}"
}

# Allow SA to read from the data bucket (where PDFs are stored for indexing)
resource "google_storage_bucket_iam_member" "sa_data_bucket_access" {
  bucket = google_storage_bucket.data_bucket.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${local.sa_email}"
}

# Allow SA to write to Firestore (Datastore User)
resource "google_project_iam_member" "sa_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${local.sa_email}"
}
