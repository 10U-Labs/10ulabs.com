data "terraform_remote_state" "api" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "api_common_routing/terraform.tfstate"
    region = "us-east-2"
  }
}
