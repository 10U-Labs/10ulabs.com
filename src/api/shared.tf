module "shared" {
  source = "../modules/shared"
}

locals {
  domain_subdomain = "api.${module.shared.domain_name}"
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
}
