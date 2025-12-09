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

  # GitHub App SSM parameters
  github_app_ssm = {
    prefix          = module.shared.github_app.ssm_prefix
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
    Agent       = "workflow-fixer"
  }
}
