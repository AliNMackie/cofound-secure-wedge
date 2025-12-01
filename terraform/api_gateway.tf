# ------------------------------------------------------------------------------
# API Gateway Service Account
# ------------------------------------------------------------------------------

resource "google_service_account" "api_gateway_sa" {
  account_id   = "ir35-api-gateway"
  display_name = "API Gateway Service Account"
  description  = "Service Account for IR35 Assessment API Gateway"
}

# ------------------------------------------------------------------------------
# API Definition
# ------------------------------------------------------------------------------

resource "google_api_gateway_api" "ir35_api" {
  provider     = google-beta
  api_id       = var.api_gateway_name
  display_name = "IR35 Assessment API"

  labels = {
    environment = var.environment
    component   = "api-gateway"
  }
}

# ------------------------------------------------------------------------------
# API Config
# ------------------------------------------------------------------------------

resource "google_api_gateway_api_config" "ir35_api_config" {
  provider             = google-beta
  api                  = google_api_gateway_api.ir35_api.api_id
  api_config_id_prefix = "ir35-api-config-"
  display_name         = "IR35 API Config"

  openapi_documents {
    document {
      path = "spec.yaml"
      contents = base64encode(templatefile("${path.module}/../security/openapi-spec.yaml", {
        PROJECT_ID         = var.project_id
        REGION             = var.region
        ASSESSMENT_API_URL = google_cloudfunctions2_function.assessment_api.service_config[0].uri
      }))
    }
  }

  gateway_config {
    backend_config {
      google_service_account = google_service_account.api_gateway_sa.email
    }
  }

  labels = {
    environment = var.environment
    component   = "api-gateway"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ------------------------------------------------------------------------------
# API Gateway
# ------------------------------------------------------------------------------

resource "google_api_gateway_gateway" "ir35_gateway" {
  provider     = google-beta
  api_config   = google_api_gateway_api_config.ir35_api_config.id
  gateway_id   = var.api_gateway_name
  display_name = "IR35 API Gateway"
  region       = var.region

  labels = {
    environment = var.environment
    component   = "api-gateway"
  }
}

# ------------------------------------------------------------------------------
# IAM Bindings
# ------------------------------------------------------------------------------

# Allow Gateway SA to invoke the Assessment Cloud Function
resource "google_cloud_run_service_iam_member" "gateway_invoker" {
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.assessment_api.name # For Gen 2, service name matches function name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.api_gateway_sa.email}"
}
