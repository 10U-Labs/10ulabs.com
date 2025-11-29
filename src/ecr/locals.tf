locals {
  aws_region          = module.shared.aws_region
  ecr_repository_name = module.shared.ecr_repository_name
  resource_prefix     = module.shared.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "ecr"
  }
}
