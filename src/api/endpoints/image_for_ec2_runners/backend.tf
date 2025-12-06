terraform {
  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "image_for_ec2_runners/terraform.tfstate"
    region       = "us-east-2"
    encrypt      = true
    use_lockfile = true
  }

  required_version = ">= 1.14"

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
