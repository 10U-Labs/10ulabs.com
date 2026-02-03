# Remote state data sources

data "terraform_remote_state" "bootstrap" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-2"
  }
}

data "terraform_remote_state" "runners_ecs" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "runners/ecs/terraform.tfstate"
    region = "us-east-2"
  }
}
