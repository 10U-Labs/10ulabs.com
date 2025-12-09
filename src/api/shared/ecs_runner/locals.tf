# Local variables for ECS runner shared infrastructure
locals {
  aws_region = module.shared.aws_region

  # ECR configuration
  ecr_repository_name = "runners"

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "api-shared-ecs-runner"
  }
}
