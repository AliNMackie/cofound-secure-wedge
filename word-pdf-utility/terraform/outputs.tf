output "service_url" {
  value       = google_cloud_run_service.default.status[0].url
  description = "The URL of the Cloud Run service"
}

output "bucket_name" {
  value       = google_storage_bucket.vault.name
  description = "The name of the GCS bucket"
}

output "service_account_email" {
  value       = google_service_account.sentinel_sa.email
  description = "The email of the Service Account"
}

output "artifact_registry_repo" {
    value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sentinel_repo.repository_id}"
    description = "The path to the Artifact Registry repository"
}
