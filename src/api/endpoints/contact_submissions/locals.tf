locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  domain_name      = module.common.domain_name
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  contact_handler_role_name = "${module.common.resource_prefix}ContactHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "contact-form"
  }
}
