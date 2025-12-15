locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  aws_account_id  = module.shared.aws_account_id
  resource_prefix = module.shared.resource_prefix

  # Runtime naming (direct code deploy - no Docker/ECR)
  runtime_name = "agent-runtime"
  stack_name   = "${local.resource_prefix}-${local.runtime_name}"

  # Lambda naming
  lambda_name    = "${local.resource_prefix}AgentWebhook"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # GitHub App SSM parameters
  github_app_ssm = {
    prefix          = module.shared.github_app.ssm_prefix
    id              = "${module.shared.github_app.ssm_prefix}/id"
    installation_id = "${module.shared.github_app.ssm_prefix}/installation_id"
    private_key     = "${module.shared.github_app.ssm_prefix}/private_key"
  }
  github_app_ssm_arns = module.shared.github_app_ssm_arns

  # Common tags
  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
  }
}
