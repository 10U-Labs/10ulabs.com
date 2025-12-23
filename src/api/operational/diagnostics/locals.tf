locals {
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"

  diagnostics_handler_role_name = "${module.shared.resource_prefix}DiagnosticsHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "diagnostics-endpoint"
  }
}
