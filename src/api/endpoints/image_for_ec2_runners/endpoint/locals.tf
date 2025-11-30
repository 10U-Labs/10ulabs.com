locals {
  aws_region         = module.shared.aws_region
  github_repo_full   = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix    = module.shared.resource_prefix
  ami_purpose_tag    = "Purpose"
  ami_purpose_value  = "GitHub self-hosted EC2 runner"
  ami_stable_tag     = "Stable"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "image-for-ec2-runners"
  }
}
