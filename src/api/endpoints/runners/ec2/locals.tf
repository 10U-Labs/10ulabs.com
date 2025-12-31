locals {
  aws_account_id               = module.common.aws_account_id
  aws_region                   = module.common.aws_region
  ec2_runner_ami_purpose_tag   = "Purpose"
  ec2_runner_ami_purpose_value = "GitHub self-hosted EC2 runner"
  ec2_runner_ami_stable_tag    = "Stable"
  ec2_runner_managed_by_tag    = "api-ec2-runner"
  github_repo_full             = "${module.common.github_org}/${module.common.name_for_github_repo}"
  lambda_role_name             = "${module.common.resource_prefix}EC2RunnerLambdaRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ec2-runner"
  }
}
