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
    lambda_function_arn  = ""
    lambda_function_name = ""
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

data "terraform_remote_state" "image_for_docker_runners" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "image_for_docker_runners/terraform.tfstate"
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

data "terraform_remote_state" "docker_runner" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "api/endpoints/docker_runner/terraform.tfstate"
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
    lambda_function_arn  = ""
    lambda_function_name = ""
  }
}
