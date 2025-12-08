locals {
  aws_region      = "us-east-2"
  aws_account_id  = "781581267945"
  resource_prefix = "TenULabs"

  # Agent naming
  agent_name    = "workflow-fixer"
  stack_name    = "${local.resource_prefix}-${local.agent_name}"
  ecr_repo_name = "${lower(local.resource_prefix)}-${local.agent_name}-agent"
  image_tag     = "latest"

  # Lambda naming
  lambda_name    = "${local.resource_prefix}WorkflowFixerWebhook"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # SSM parameters
  ssm_github_pat = "/${local.resource_prefix}/github_pat"

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "workflow-fixer"
  }
}
