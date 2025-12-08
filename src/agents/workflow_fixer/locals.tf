locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  # Agent naming
  agent_name    = "workflow-fixer"
  stack_name    = "${local.resource_prefix}-${local.agent_name}"
  ecr_repo_name = "${lower(local.resource_prefix)}-${local.agent_name}-agent"
  image_tag     = "latest"

  # Lambda naming
  lambda_name    = "${local.resource_prefix}WorkflowFixerWebhook"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # SSM parameters
  ssm_github_pat     = module.shared.ssm_github_pat_name
  ssm_github_pat_arn = module.shared.ssm_github_pat_arn

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "workflow-fixer"
  }
}
