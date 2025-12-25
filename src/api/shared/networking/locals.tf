locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  # VPC configuration
  vpc_name                = "${local.resource_prefix}RunnersVpc"
  vpc_cidr                = "10.0.0.0/16"
  vpc_max_azs             = 99
  public_subnet_cidr_mask = 24
  vpc_azs                 = slice(data.aws_availability_zones.available.names, 0, min(length(data.aws_availability_zones.available.names), local.vpc_max_azs))

  # Common tags
  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "api-shared-runners"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}
