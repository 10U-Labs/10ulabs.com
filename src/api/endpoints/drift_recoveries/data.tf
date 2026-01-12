data "terraform_remote_state" "api_common_networking" {
  backend = "s3"
  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/common/networking/terraform.tfstate"
    region = module.common.aws_region
  }
}

data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}
