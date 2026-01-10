# Remote state data sources

data "terraform_remote_state" "github_workflows_retries" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "github_workflows/retries/terraform.tfstate"
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
