data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/terraform.tfstate"
    region = local.aws_region
  }
}

data "terraform_remote_state" "website" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "website/terraform.tfstate"
    region = local.aws_region
  }
}
