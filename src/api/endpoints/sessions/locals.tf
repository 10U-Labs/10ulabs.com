locals {
  aws_region      = module.common.aws_region
  aws_account_id  = module.common.aws_account_id
  resource_prefix = module.common.resource_prefix

  export_function_name          = "${module.common.resource_prefix}SessionsExport"
  crawler_trigger_function_name = "${module.common.resource_prefix}SessionsCrawlerTrigger"

  export_role_name          = "${module.common.resource_prefix}SessionsExportRole"
  glue_crawler_role_name    = "${module.common.resource_prefix}SessionsGlueCrawlerRole"
  scheduler_role_name       = "${module.common.resource_prefix}SessionsSchedulerRole"
  crawler_trigger_role_name = "${module.common.resource_prefix}SessionsCrawlerTriggerRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "sessions"
  }
}
