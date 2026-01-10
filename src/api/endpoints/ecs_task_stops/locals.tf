locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  resource_prefix  = module.common.resource_prefix
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name    = "${local.resource_prefix}EcsTaskStops"
  lambda_role_name = "${local.resource_prefix}EcsTaskStopsRole"
  queue_name       = "${local.resource_prefix}EcsTaskStops"
  dlq_name         = "${local.resource_prefix}EcsTaskStopsDlq"
  rule_name        = "${local.resource_prefix}EcsTaskStoppedRule"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ecs-task-stops"
  }
}
