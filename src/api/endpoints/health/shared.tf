module "shared" {
  source = "../../../../lib/terraform"
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "api/terraform.tfstate"
    region = "us-east-2"
  }
}
