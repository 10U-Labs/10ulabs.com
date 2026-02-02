locals {
  aws_region      = module.common.aws_region
  aws_account_id  = module.common.aws_account_id
  resource_prefix = module.common.resource_prefix

  export_function_name = "${module.common.resource_prefix}SessionsExport"
  export_role_name     = "${module.common.resource_prefix}SessionsExportRole"
  scheduler_role_name  = "${module.common.resource_prefix}SessionsSchedulerRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "sessions"
  }
}
