data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "jit_runner_requests" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "webhooks/github/jit_runner_requests/terraform.tfstate"
    region = "us-east-2"
  }

  defaults = {
    lambda_function_arn               = ""
    lambda_function_name              = ""
    security_group_id_for_runners     = ""
    ssm_parameter_name_for_latest_ami = ""
    public_subnets_ids                 = ""
  }
}

data "terraform_remote_state" "health" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "health/terraform.tfstate"
    region = "us-east-2"
  }

  defaults = {
    lambda_function_arn  = ""
    lambda_function_name = ""
    log_group_name       = ""
  }
}

