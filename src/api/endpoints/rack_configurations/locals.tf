locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  # Lambda function names (single source of truth)
  export_function_name          = "${module.common.resource_prefix}RackDesignerExport"
  crawler_trigger_function_name = "${module.common.resource_prefix}RackDesignerCrawlerTrigger"

  # IAM role names (single source of truth)
  handler_role_name         = "${module.common.resource_prefix}RackDesignerLambdaRole"
  export_role_name          = "${module.common.resource_prefix}RackDesignerExportRole"
  glue_crawler_role_name    = "${module.common.resource_prefix}RackDesignerGlueCrawlerRole"
  scheduler_role_name       = "${module.common.resource_prefix}RackDesignerSchedulerRole"
  crawler_trigger_role_name = "${module.common.resource_prefix}RackDesignerCrawlerTriggerRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-designer"
  }
}
