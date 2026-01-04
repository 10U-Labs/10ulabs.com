locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  handler_role_name = "${module.common.resource_prefix}RackConfigurationsLambdaRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-configurations"
  }
}
