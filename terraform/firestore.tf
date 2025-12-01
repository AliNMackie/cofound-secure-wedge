# ------------------------------------------------------------------------------
# Firestore Database
# ------------------------------------------------------------------------------

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.firestore_region
  type        = "FIRESTORE_NATIVE"

  # Using Native mode to support the Collection/Document model used by the Python code.
  # (Datastore mode uses Entities/Kinds which differs from the firestore.Client() usage).
}

# ------------------------------------------------------------------------------
# Security Rules
# ------------------------------------------------------------------------------

resource "google_firebaserules_ruleset" "firestore_rules" {
  provider = google-beta
  project  = var.project_id

  source {
    files {
      name = "firestore.rules"
      content = templatefile("${path.module}/../security/firestore.rules", {
        PROJECT_ID = var.project_id
      })
    }
  }
}

resource "google_firebaserules_release" "release" {
  provider     = google-beta
  name         = "cloud.firestore" # This releases to the default database
  ruleset_name = google_firebaserules_ruleset.firestore_rules.name
  project      = var.project_id

  depends_on = [
    google_firestore_database.database
  ]
}
