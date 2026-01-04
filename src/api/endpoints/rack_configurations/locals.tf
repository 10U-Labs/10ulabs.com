locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  handler_role_name     = "${local.resource_prefix}RackConfigurationsLambdaRole"
  backup_vault_name     = "${local.resource_prefix}-rack-configurations-backup"
  backup_role_name      = "${local.resource_prefix}RackConfigurationsBackupRole"
  backup_selection_name = "${local.resource_prefix}-rack-configurations-tables"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-configurations"
  }
}
