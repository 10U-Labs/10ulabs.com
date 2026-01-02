locals {
  aws_region      = module.common.aws_region
  aws_account_id  = module.common.aws_account_id
  resource_prefix = module.common.resource_prefix

  common_tags = {
    Application = "Sessions"
    Environment = "Production"
  }
}
