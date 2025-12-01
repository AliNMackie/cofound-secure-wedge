output "vertex_ai_index_id" {
  description = "The ID of the Vertex AI Index"
  value       = google_vertex_ai_index.index.id
}

output "vertex_ai_endpoint_id" {
  description = "The ID of the Vertex AI Index Endpoint"
  value       = google_vertex_ai_index_endpoint.endpoint.id
}

output "vertex_ai_endpoint_name" {
  description = "The full resource name of the Vertex AI Index Endpoint"
  value       = google_vertex_ai_index_endpoint.endpoint.name
}

output "deployed_index_id" {
  description = "The ID of the deployed index"
  value       = google_vertex_ai_index_endpoint_deployed_index.deployment.deployed_index_id
}

output "api_gateway_endpoint" {
  description = "The base URL of the API Gateway"
  value       = google_api_gateway_gateway.ir35_gateway.default_hostname
}

output "api_gateway_service_account_email" {
  description = "The email of the API Gateway Service Account"
  value       = google_service_account.api_gateway_sa.email
}

output "firestore_database_id" {
  description = "The ID of the Firestore Database"
  value       = google_firestore_database.database.name
}

output "firestore_rules_status" {
  description = "The status of the Firestore Security Rules release"
  value       = google_firebaserules_release.release.name
}
