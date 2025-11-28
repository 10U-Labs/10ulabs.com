locals {
  aws_region            = module.shared.aws_region
  domain_name           = module.shared.domain_name
  apex_fqdn             = module.shared.domain_name
  www_fqdn              = "www.${module.shared.domain_name}"
  github_repo_full      = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  name_for_central_logs = module.shared.name_for_central_logs_bucket

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "website-infrastructure"
  }
}
