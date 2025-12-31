data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }

  defaults = {
    api_gateway_id   = ""
    api_key_ssm_parameter     = ""
    api_key_ssm_parameter_arn = ""
  }
}
