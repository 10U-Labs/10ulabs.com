data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "wan_synthesizer" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "wan-synthesizer/common/routing/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "api_10ulabs_com" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "api.10ulabs.com/src/api/common/routing/terraform.tfstate"
    region = "us-east-2"
  }
}

