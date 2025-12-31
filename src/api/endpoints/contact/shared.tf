module "common" {
  source = "../../../../lib/terraform/common"
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.common.aws_region
  }
}
