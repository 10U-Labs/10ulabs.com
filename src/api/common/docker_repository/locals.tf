# Local variables for Docker repository shared infrastructure
locals {
  aws_region = module.common.aws_region

  # ECR configuration
  ecr_repository_name = "runners"

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "api-shared-docker-repository"
  }
}
