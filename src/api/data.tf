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

data "aws_ssm_parameter" "github_pat" {
  name            = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
  with_decryption = true
}
