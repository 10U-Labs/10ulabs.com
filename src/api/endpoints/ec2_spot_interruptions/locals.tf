locals {
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  resource_prefix  = module.common.resource_prefix
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name    = "${local.resource_prefix}EC2SpotInterruptions"
  lambda_role_name = "${local.resource_prefix}EC2SpotInterruptionsRole"
  queue_name       = "${local.resource_prefix}EC2SpotInterruptions"
  dlq_name         = "${local.resource_prefix}EC2SpotInterruptionsDlq"
  rule_name        = "${local.resource_prefix}EC2SpotInterruptionRule"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ec2-spot-interruptions"
  }
}
