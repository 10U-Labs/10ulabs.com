data "terraform_remote_state" "bootstrap" {
  backend = "s3"

  config = {
    bucket = "10ulabs-terraform-state"
    key    = "bootstrap/terraform.tfstate"
    region = "us-east-1"
  }
}
