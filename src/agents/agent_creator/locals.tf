locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  agent_name = "agent-creator"
  stack_name = "${local.resource_prefix}-${local.agent_name}"
  image_tag  = "${local.agent_name}-latest"

  lambda_name    = "${local.resource_prefix}AgentCreator"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # GitHub App SSM parameters
  github_app_ssm = {
    id              = "${module.shared.github_app.ssm_prefix}/id"
    installation_id = "${module.shared.github_app.ssm_prefix}/installation_id"
    private_key     = "${module.shared.github_app.ssm_prefix}/private_key"
  }
  github_app_ssm_arns = module.shared.github_app_ssm_arns

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "agent-creator"
  }
}
