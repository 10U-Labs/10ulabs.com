locals {
  aws_region          = "us-east-2"
  aws_account_id      = data.aws_caller_identity.current.account_id
  resource_prefix     = "TenULabs"
  ssm_github_pat_name = "/github/pat"

  # AgentCore shared infrastructure
  agentcore = {
    execution_role_name = "${local.resource_prefix}AgentCoreExecutionRole"
    execution_role_arn  = "arn:aws:iam::${local.aws_account_id}:role/${local.resource_prefix}AgentCoreExecutionRole"
  }

  # GitHub App configuration
  github_app = {
    id              = "2436221"
    installation_id = "98653544"
    ssm_prefix      = "/github/app"
  }

  lambda_handler_names = {
    catchall            = "${local.resource_prefix}CatchAllHandler"
    contact             = "${local.resource_prefix}ContactHandler"
    echo                = "${local.resource_prefix}DiagnosticsHandler"
    health              = "${local.resource_prefix}HealthHandler"
    rack_configurations = "${local.resource_prefix}RackConfigurationsHandler"
    sessions            = "${local.resource_prefix}SessionsHandler"
  }
}
