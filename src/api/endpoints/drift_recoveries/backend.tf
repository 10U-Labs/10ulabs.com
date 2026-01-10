terraform {
  required_version = ">= 1.9.0"

  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "drift_recoveries/terraform.tfstate"
    region       = "us-east-2"
    use_lockfile = true
  }
}
