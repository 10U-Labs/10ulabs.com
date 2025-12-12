locals {
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  domain_name      = module.shared.domain_name
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"

  contact_handler_role_name = "ContactHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "contact-form"
  }
}
