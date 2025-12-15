locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  # ECR repository name
  ecr_repository_name = "agents"

  # Common tags
  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents-shared"
  }
}
