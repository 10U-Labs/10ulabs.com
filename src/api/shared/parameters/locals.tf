locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  resource_prefix = module.shared.resource_prefix

  # SSM parameter names (from shared module for consistency)
  ssm_ec2_runner_ami_latest = module.shared.ssm_ec2_runner_ami_latest

  # Common tags
  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "api-shared-parameters"
  }
}
