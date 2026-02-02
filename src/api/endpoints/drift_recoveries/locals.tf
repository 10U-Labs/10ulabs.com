locals {
  resource_prefix = module.common.resource_prefix
  github_repo     = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name    = "${local.resource_prefix}DriftRecoveries"
  lambda_role_name = "${local.resource_prefix}DriftRecoveriesRole"
  alert_email      = "jdrowne@10ulabs.com"

  common_tags = {
    ManagedBy = "Terraform"
    Purpose   = "DriftRecoveries"
  }
}
