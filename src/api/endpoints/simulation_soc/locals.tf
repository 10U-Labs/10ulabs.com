locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  resource_prefix  = module.common.resource_prefix
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  # Lambda configuration (single source of truth)
  handler_log_group = "/aws/lambda/${module.common.lambda_handler_names.simulation_soc}"
  handler_role_name = "${local.resource_prefix}SimulationSocHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "simulation-soc-endpoint"
  }
}
