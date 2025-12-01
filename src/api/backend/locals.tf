locals {
  api_fqdn       = "api.${module.shared.domain_name}"
  aws_account_id = module.shared.aws_account_id
  aws_region     = module.shared.aws_region
  domain_name    = module.shared.domain_name
  github_org     = module.shared.github_org
  github_repo    = module.shared.name_for_github_repo
  github_repo_full   = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix    = module.shared.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "API infrastructure"
  }
}
