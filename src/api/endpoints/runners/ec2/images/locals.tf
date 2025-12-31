locals {
  aws_account_id    = module.common.aws_account_id
  aws_region        = module.common.aws_region
  github_repo_full  = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix   = module.common.resource_prefix
  ami_purpose_tag   = "Purpose"
  ami_purpose_value = "GitHub self-hosted EC2 runner"
  ami_stable_tag    = "Stable"
  lambda_role_name  = "${local.resource_prefix}ImageForEC2RunnersHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "image-for-ec2-runners"
  }
}
