data "terraform_remote_state" "common_shared" {
  backend = "s3"
  config = {
    bucket = "10ulabs-terraform-state-us-east-2"
    key    = "common/shared/terraform.tfstate"
    region = "us-east-2"
  }
}

data "aws_kms_alias" "ssm" {
  name = "alias/aws/ssm"
}
