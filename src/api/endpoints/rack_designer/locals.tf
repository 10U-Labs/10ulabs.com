locals {
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix  = module.shared.resource_prefix

  # Lambda function names (single source of truth)
  export_function_name          = "${module.shared.resource_prefix}RackDesignerExport"
  crawler_trigger_function_name = "${module.shared.resource_prefix}RackDesignerCrawlerTrigger"

  # IAM role names (single source of truth)
  handler_role_name         = "${module.shared.resource_prefix}RackDesignerLambdaRole"
  export_role_name          = "${module.shared.resource_prefix}RackDesignerExportRole"
  glue_crawler_role_name    = "${module.shared.resource_prefix}RackDesignerGlueCrawlerRole"
  scheduler_role_name       = "${module.shared.resource_prefix}RackDesignerSchedulerRole"
  crawler_trigger_role_name = "${module.shared.resource_prefix}RackDesignerCrawlerTriggerRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-designer"
  }
}
