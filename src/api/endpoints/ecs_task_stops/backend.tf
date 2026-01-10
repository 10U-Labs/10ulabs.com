terraform {
  required_version = ">= 1.9.0"

  backend "s3" {
    bucket       = "10ulabs-terraform-state-us-east-2"
    key          = "ecs_task_stops/terraform.tfstate"
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
