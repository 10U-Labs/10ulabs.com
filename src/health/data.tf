data "terraform_remote_state" "api" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "api/terraform.tfstate"
    region = "us-east-1"
  }
}
