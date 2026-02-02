locals {
  resource_prefix  = module.common.resource_prefix

  function_name    = "${local.resource_prefix}EC2SpotInterruptions"
  lambda_role_name = "${local.resource_prefix}EC2SpotInterruptionsRole"
  rule_name        = "${local.resource_prefix}EC2SpotInterruptionRule"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ec2-spot-interruptions"
  }
}
