data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "bootstrap/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api_shared_ecs_runner" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/ecs_runner/terraform.tfstate"
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
