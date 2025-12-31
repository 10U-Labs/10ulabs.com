data "terraform_remote_state" "api_common_routing" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api_common_networking" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/common/networking/terraform.tfstate"
    region = local.aws_region
  }
}
