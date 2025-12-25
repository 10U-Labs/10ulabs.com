data "terraform_remote_state" "api_shared_docker_repository" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/docker_repository/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }
}
