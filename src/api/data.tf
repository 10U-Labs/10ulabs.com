data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_ssm_parameter" "github_pat" {
  name            = data.terraform_remote_state.bootstrap.outputs.github_pat_parameter_name
  with_decryption = true
}
