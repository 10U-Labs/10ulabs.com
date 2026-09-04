locals {
  aws_region      = module.common.aws_region
  aws_account_id  = module.common.aws_account_id
  resource_prefix = module.common.resource_prefix

  export_function_name = "${module.common.resource_prefix}SessionsExport"
  export_role_name     = "${module.common.resource_prefix}SessionsExportRole"
  scheduler_role_name  = "${module.common.resource_prefix}SessionsSchedulerRole"
  handler_role_name    = "${module.common.resource_prefix}SessionsHandlerRole"
  dynamodb_table_name  = "${module.common.resource_prefix}-session-events"
  s3_bucket_name       = "${lower(module.common.resource_prefix)}-sessions-analytics"

  export_log_group_tag_name  = "${module.common.resource_prefix}-SessionsExport-Logs"
  daily_export_schedule_name = "${module.common.resource_prefix}-SessionsDailyExport"

  backup_vault_name     = "${module.common.resource_prefix}-sessions-backup"
  backup_role_name      = "${module.common.resource_prefix}SessionsBackupRole"
  backup_selection_name = "${module.common.resource_prefix}-sessions-tables"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "sessions"
  }
}
