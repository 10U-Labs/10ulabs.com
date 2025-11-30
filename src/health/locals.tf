locals {
  aws_region       = module.shared.aws_region
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "health-check"
  }
}
