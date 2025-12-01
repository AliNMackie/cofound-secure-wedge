terraform {
  backend "gcs" {
    # The bucket name cannot be a variable in the backend block.
    # Please replace replace-with-your-project-id with your actual project ID.
    bucket = "replace-with-your-project-id-tfstate"
    prefix = "terraform/state"
  }
}
