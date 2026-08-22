data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.common.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.common.aws_region
  }

  defaults = {
    cloudwatch_logs_firehose_role_arn = ""
    firehose_cloudwatch_logs_arn      = ""
  }
}

data "aws_ssm_parameter" "github_pat" {
  name            = module.common.ssm_github_pat_name
  with_decryption = true
}
