locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  # Lambda function names (single source of truth)
  export_function_name          = "${module.common.resource_prefix}RackConfigurationsExport"
  crawler_trigger_function_name = "${module.common.resource_prefix}RackConfigurationsCrawlerTrigger"

  # IAM role names (single source of truth)
  handler_role_name         = "${module.common.resource_prefix}RackConfigurationsLambdaRole"
  export_role_name          = "${module.common.resource_prefix}RackConfigurationsExportRole"
  glue_crawler_role_name    = "${module.common.resource_prefix}RackConfigurationsGlueCrawlerRole"
  scheduler_role_name       = "${module.common.resource_prefix}RackConfigurationsSchedulerRole"
  crawler_trigger_role_name = "${module.common.resource_prefix}RackConfigurationsCrawlerTriggerRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-configurations"
  }
}
