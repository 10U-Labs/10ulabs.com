locals {
  resource_prefix  = module.common.resource_prefix
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name    = "${local.resource_prefix}RunnersCleanups"
  lambda_role_name = "${local.resource_prefix}RunnersCleanupRole"
  schedule_name    = "${local.resource_prefix}RunnersCleanupSchedule"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "runners-cleanups"
  }
}
