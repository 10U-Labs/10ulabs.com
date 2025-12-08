locals {
  aws_region      = "us-east-2"
  aws_account_id  = "781581267945"
  resource_prefix = "TenULabs"

  agent_name    = "agent-creator"
  stack_name    = "${local.resource_prefix}-${local.agent_name}"
  ecr_repo_name = "${lower(local.resource_prefix)}-${local.agent_name}-agent"
  image_tag     = "latest"

  lambda_name    = "${local.resource_prefix}AgentCreator"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  ssm_github_pat = "/${local.resource_prefix}/github_pat"

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "agent-creator"
  }
}
