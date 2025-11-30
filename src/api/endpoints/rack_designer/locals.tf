locals {
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix  = module.shared.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "rack-designer"
  }
}
