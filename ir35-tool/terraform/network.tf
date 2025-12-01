# ------------------------------------------------------------------------------
# Serverless VPC Access Connector
# ------------------------------------------------------------------------------

resource "google_vpc_access_connector" "connector" {
  name          = "ir35-vpc-connector"
  region        = var.region
  network       = var.network
  ip_cidr_range = "10.8.0.0/28"
}
