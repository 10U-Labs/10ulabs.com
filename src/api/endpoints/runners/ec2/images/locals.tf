locals {
  aws_account_id    = module.common.aws_account_id
  aws_region        = module.common.aws_region
  github_repo_full  = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix   = module.common.resource_prefix
  ami_purpose_tag   = module.common.runners_config.tags.ec2.ami.purpose_tag
  ami_purpose_value = module.common.runners_config.tags.ec2.ami.purpose_value
  ami_stable_tag    = module.common.runners_config.tags.ec2.ami.stable_tag
  ami_stable_value  = module.common.runners_config.tags.ec2.ami.stable_value
  lambda_role_name  = "${local.resource_prefix}ImageForEC2RunnersHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "image-for-ec2-runners"
  }
}
