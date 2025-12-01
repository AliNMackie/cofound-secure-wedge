# ------------------------------------------------------------------------------
# Vertex AI Matching Engine (Vector Search)
# ------------------------------------------------------------------------------

locals {
  # Use the provided SA email if available, otherwise use the one created in main.tf
  sa_email = var.cloud_function_sa_email != "" ? var.cloud_function_sa_email : google_service_account.cloud_function_sa.email
}

# Bucket for initial index data (required by some provider versions even for STREAM_UPDATE)
resource "google_storage_bucket" "data_bucket" {
  name          = "${var.project_id}-rag-data"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    component   = "rag-indexer"
  }
}

resource "google_vertex_ai_index" "index" {
  region       = var.vertex_ai_region
  display_name = "ir35-cest-guidelines-index"
  description  = "Vector index for CEST guidelines and case law"

  index_update_method = "STREAM_UPDATE"

  metadata {
    # Point to the created bucket to satisfy validation/deployment requirements
    contents_delta_uri = "gs://${google_storage_bucket.data_bucket.name}/initial-index"

    config {
      dimensions                  = var.index_dimensions
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"
      approximate_neighbors_count = 150 # Standard default

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 500
        }
      }
    }
  }

  labels = {
    environment = var.environment
    component   = "rag-indexer"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_vertex_ai_index_endpoint" "endpoint" {
  region       = var.vertex_ai_region
  display_name = "ir35-assessment-endpoint"
  description  = "Endpoint for IR35 assessment queries"
  network      = "projects/${var.project_id}/global/networks/${var.network}"

  # Note: Connecting to a private VPC requires Private Service Access (VPC Peering) 
  # to be configured in the network. This is a prerequisite.
  public_endpoint_enabled = false

  labels = {
    environment = var.environment
    component   = "assessment-api"
  }
}

resource "google_vertex_ai_index_endpoint_deployed_index" "deployment" {
  index_endpoint    = google_vertex_ai_index_endpoint.endpoint.id
  index             = google_vertex_ai_index.index.id
  deployed_index_id = "ir35_cest_deployed"

  dedicated_resources {
    machine_spec {
      machine_type = var.vertex_ai_machine_type
    }
    min_replica_count = var.min_replicas
    max_replica_count = var.max_replicas
  }

  # Ensure the index and endpoint are fully created/ready before deploying
  depends_on = [
    google_vertex_ai_index.index,
    google_vertex_ai_index_endpoint.endpoint
  ]
}

# ------------------------------------------------------------------------------
# IAM Bindings
# ------------------------------------------------------------------------------

# Grant Cloud Function service account permission to query the index
resource "google_project_iam_member" "sa_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${local.sa_email}"
}

# Grant Cloud Function service account permission to read metadata
resource "google_project_iam_member" "sa_vertex_viewer" {
  project = var.project_id
  role    = "roles/aiplatform.viewer"
  member  = "serviceAccount:${local.sa_email}"
}
