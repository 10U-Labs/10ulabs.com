data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "runners/terraform.tfstate"
    region = "us-east-1"
  }

  defaults = {
    lambda_function_arn      = ""
    lambda_function_name     = ""
    runner_security_group_id = ""
    vpc_public_subnet_ids    = ""
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

data "terraform_remote_state" "image_for_ecs_runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "image_for_ecs_runners/terraform.tfstate"
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

data "terraform_remote_state" "ecs_runner" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "api/endpoints/ecs_runner/terraform.tfstate"
    region = "us-east-1"
  }

  defaults = {
    lambda_function_arn  = ""
    lambda_function_name = ""
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
    ec2_instance_types           = []
    ec2_runner_ami_purpose_value = ""
    ec2_runner_ami_stable_tag    = ""
    lambda_function_arn          = ""
    lambda_function_name         = ""
  }
}

data "terraform_remote_state" "simulation_soc" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "simulation_soc/terraform.tfstate"
    region = "us-east-1"
  }
}
