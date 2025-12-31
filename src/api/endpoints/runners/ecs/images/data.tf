data "terraform_remote_state" "api_common_docker_repository" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/common/docker_repository/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }
}
