data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "bootstrap/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api_shared_networking" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/networking/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "api_shared_routing" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }

  defaults = {
    api_fqdn                  = ""
    api_gateway_id   = ""
    api_key_ssm_parameter     = ""
    api_key_ssm_parameter_arn = ""
  }
}

