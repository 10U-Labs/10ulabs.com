locals {
  aws_account_id               = module.shared.aws_account_id
  aws_region                   = module.shared.aws_region
  ec2_runner_ami_purpose_tag   = "Purpose"
  ec2_runner_ami_purpose_value = module.shared.ec2_runner_ami_purpose_value
  ec2_runner_ami_stable_tag    = module.shared.ec2_runner_ami_stable_tag
  ec2_runner_managed_by_tag    = "api-ec2-runner"
  github_repo_full             = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  lambda_role_name             = "${module.shared.resource_prefix}EC2RunnerLambdaRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ec2-runner"
  }
}
