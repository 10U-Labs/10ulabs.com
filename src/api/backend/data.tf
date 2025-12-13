data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "runners/terraform.tfstate"
    region = "us-east-2"
  }

  defaults = {
    lambda_function_arn               = ""
    lambda_function_name              = ""
    runner_security_group_id          = ""
    ssm_parameter_name_for_latest_ami = ""
    vpc_public_subnet_ids             = ""
    webhook_ingress_queue_url         = ""
    webhook_ingress_queue_arn         = ""
    webhook_ingress_queue_name        = ""
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

data "terraform_remote_state" "ec2_runner" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "ec2_runner/terraform.tfstate"
    region = "us-east-2"
  }

  defaults = {
    ec2_instance_types           = []
    ec2_runner_ami_purpose_value = ""
    ec2_runner_ami_stable_tag    = ""
    lambda_function_arn          = ""
    lambda_function_name         = ""
  }
}

