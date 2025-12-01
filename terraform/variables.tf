variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "europe-west2"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "sentinel-growth"
}

variable "bucket_name" {
  description = "The name of the GCS bucket"
  type        = string
  default     = "sentinel-growth-artifacts" 
}
