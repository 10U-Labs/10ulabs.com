# Local variables for ECS runner shared infrastructure
locals {
  aws_region      = module.shared.aws_region
  aws_account_id  = module.shared.aws_account_id
  resource_prefix = module.shared.resource_prefix

  # ECR configuration
  ecr_repository_name = "runners"

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "api-shared-ecs-runner"
  }
}
