locals {
  aws_region            = module.common.aws_region
  domain_name           = module.common.domain_name
  apex_fqdn             = module.common.domain_name
  www_fqdn              = "www.${module.common.domain_name}"
  website_bucket_name   = "www-${replace(module.common.domain_name, ".", "-")}"
  github_repo_full      = "${module.common.github_org}/${module.common.name_for_github_repo}"
  name_for_central_logs = module.common.name_for_central_logs_bucket
  resource_prefix       = "${module.common.resource_prefix}Website"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "website-infrastructure"
  }
}
