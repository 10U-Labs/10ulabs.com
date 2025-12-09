data "terraform_remote_state" "agents_shared" {
  backend = "s3"

  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "agents/shared/terraform.tfstate"
    region = local.aws_region
  }
}
