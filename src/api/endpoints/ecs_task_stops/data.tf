# Remote state data sources

data "terraform_remote_state" "runners_ecs" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "runners/ecs/terraform.tfstate"
    region = "us-east-2"
  }
}
