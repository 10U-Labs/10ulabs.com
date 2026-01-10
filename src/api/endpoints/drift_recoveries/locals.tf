locals {
  resource_prefix = module.shared.resource_prefix
  aws_region      = module.shared.aws_region
  aws_account_id  = module.shared.aws_account_id
  github_repo     = module.shared.github_repo

  function_name           = "${local.resource_prefix}DriftRecoveries"
  lambda_role_name        = "${local.resource_prefix}DriftRecoveriesRole"
  queue_name              = "${local.resource_prefix}DriftRecoveries"
  config_recorder_role_name = "${local.resource_prefix}ConfigRecorderRole"

  common_tags = {
    ManagedBy = "Terraform"
    Purpose   = "DriftRecoveries"
  }
}
