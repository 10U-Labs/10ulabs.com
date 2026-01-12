terraform {
  required_version = ">= 1.14"

  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "ec2_spot_interruptions/terraform.tfstate"
    region       = "us-east-2"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}
