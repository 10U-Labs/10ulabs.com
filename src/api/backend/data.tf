data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "ecr" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "ecr/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "image_for_docker_runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "image_for_docker_runners/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "rack_designer" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "rack_designer/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "health" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "health/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "contact" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "contact/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "echo" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "echo/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "image_for_ec2_runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "image_for_ec2_runners/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "ec2_runner" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "ec2_runner/terraform.tfstate"
    region = "us-east-1"
  }

  defaults = {
    ec2_instance_profile_name    = ""
    ec2_max_spot_price           = ""
    ec2_runner_ami_purpose_tag   = ""
    ec2_runner_ami_purpose_value = ""
    ec2_runner_ami_stable_tag    = ""
    ec2_runner_managed_by_tag    = ""
    ec2_runner_role_arn          = ""
    ec2_runner_role_name         = ""
    ec2_spot_instance_types      = []
    lambda_function_arn          = ""
    lambda_function_name         = ""
  }
}

data "aws_ssm_parameter" "github_pat" {
  name            = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
  with_decryption = true
}
