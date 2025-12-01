data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "bootstrap/terraform.tfstate"
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
    runner_security_group_id    = ""
    vpc_id                      = ""
    vpc_public_subnet_ids       = ""
    workflow_runners_table_arn  = ""
    workflow_runners_table_name = ""
  }
}
