module "shared" {
  source = "../../../../lib/terraform"
}

data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = module.shared.aws_region
  }
}
