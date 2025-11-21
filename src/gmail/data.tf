data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state"
    key    = "foundation/terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_route53_zone" "main" {
  zone_id = data.terraform_remote_state.foundation.outputs.hosted_zone_id
}
