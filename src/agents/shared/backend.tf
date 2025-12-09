terraform {
  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "agents/shared/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true
  }
}
