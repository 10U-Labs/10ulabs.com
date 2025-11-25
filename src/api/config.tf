module "config" {
  source = "../modules/config"
}

locals {
  domain_subdomain = "api.${module.config.domain_name}"
  github_repo_full = "${module.config.github_org}/${module.config.github_repo_name}"
}
