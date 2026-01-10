# Remote state data sources

data "terraform_remote_state" "bootstrap" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "api_common_routing" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "api/common/routing/terraform.tfstate"
    region = "us-east-2"
  }
}
