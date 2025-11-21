terraform {
  backend "s3" {
    bucket       = "10ulabs-terraform-state"
    key          = "gmail/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
