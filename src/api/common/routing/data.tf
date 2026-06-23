data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "wan_graph_designer" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "wan-graph-synthesizer/common/routing/terraform.tfstate"
    region = "us-east-2"
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

