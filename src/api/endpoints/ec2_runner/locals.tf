locals {
  aws_account_id               = module.shared.aws_account_id
  aws_region                   = module.shared.aws_region
  ec2_runner_ami_purpose_tag   = "Purpose"
  ec2_runner_ami_purpose_value = "GitHub self-hosted EC2 runner"
  ec2_runner_ami_stable_tag    = "Stable"
  ec2_runner_managed_by_tag    = "api-ec2-runner"
  github_repo_full             = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix              = module.shared.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ec2-runner"
  }
}
