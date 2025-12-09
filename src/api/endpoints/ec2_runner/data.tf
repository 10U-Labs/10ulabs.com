data "terraform_remote_state" "api_shared_runners" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/runners/terraform.tfstate"
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

  defaults = {
    api_key_ssm_parameter     = ""
    api_key_ssm_parameter_arn = ""
  }
}

data "terraform_remote_state" "runners" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "runners/terraform.tfstate"
    region = local.aws_region
  }

  defaults = {
    api_endpoint                = ""
    github_token_secret_name    = ""
    workflow_runners_table_arn  = ""
    workflow_runners_table_name = ""
  }
}
