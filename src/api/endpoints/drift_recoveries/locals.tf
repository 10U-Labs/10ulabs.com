locals {
  resource_prefix = module.common.resource_prefix
  aws_account_id  = module.common.aws_account_id
  github_repo     = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name             = "${local.resource_prefix}DriftRecoveries"
  lambda_role_name          = "${local.resource_prefix}DriftRecoveriesRole"
  queue_name                = "${local.resource_prefix}DriftRecoveries"
  config_recorder_role_name = "${local.resource_prefix}ConfigRecorderRole"
  alert_email               = "jdrowne@10ulabs.com"

  common_tags = {
    ManagedBy = "Terraform"
    Purpose   = "DriftRecoveries"
  }
}
