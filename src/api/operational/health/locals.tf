locals {
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  resource_prefix  = module.shared.resource_prefix
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"

  lambda_role_name = "${local.resource_prefix}HealthHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "health-check"
  }
}
