terraform {
  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "api/common/docker_repository/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true
  }
}
