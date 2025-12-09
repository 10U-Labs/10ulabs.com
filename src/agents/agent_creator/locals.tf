locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  agent_name = "agent-creator"
  stack_name = "${local.resource_prefix}-${local.agent_name}"
  image_tag  = "${local.agent_name}-latest"

  lambda_name    = "${local.resource_prefix}AgentCreator"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # SSM parameters
  ssm_github_pat     = module.shared.ssm_github_pat_name
  ssm_github_pat_arn = module.shared.ssm_github_pat_arn

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "agent-creator"
  }
}
