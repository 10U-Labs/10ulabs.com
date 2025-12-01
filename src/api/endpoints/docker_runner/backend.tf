terraform {
  backend "s3" {
    bucket = "10ulabs-terraform-state"
    key    = "api/endpoints/docker_runner/terraform.tfstate"
    region = "us-east-1"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "aws" {
  region = module.shared.aws_region
}
