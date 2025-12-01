variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "The environment (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "cloud_function_sa_email" {
  description = "The Service Account email for Cloud Functions. If not provided, the default App Engine SA might be used or it must be created elsewhere."
  type        = string
  default     = "" # Allow empty to skip binding if not available, or we will create one.
}

variable "vertex_ai_region" {
  description = "The region for Vertex AI resources"
  type        = string
  default     = "us-central1"
}

variable "index_dimensions" {
  description = "The number of dimensions for the vector index"
  type        = number
  default     = 768
}

variable "vertex_ai_machine_type" {
  description = "The machine type for the index endpoint deployment"
  type        = string
  default     = "e2-standard-2"
}

variable "min_replicas" {
  description = "Minimum number of replicas for the index deployment"
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "Maximum number of replicas for the index deployment"
  type        = number
  default     = 2
}

variable "network" {
  description = "The VPC network name to deploy the endpoint to"
  type        = string
  default     = "default"
}

variable "api_gateway_name" {
  description = "The name of the API Gateway"
  type        = string
  default     = "ir35-assessment-api"
}

variable "firestore_region" {
  description = "The region for Firestore (e.g., us-central1 or nam5 for multi-region)"
  type        = string
  default     = "us-central1"
}
