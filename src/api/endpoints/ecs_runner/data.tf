data "terraform_remote_state" "runners" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "runners/terraform.tfstate"
    region = module.shared.aws_region
  }

  defaults = {
    api_endpoint                = ""
    ecr_repository_name         = ""
    github_token_secret_name    = ""
    runner_security_group_id    = ""
    vpc_id                      = ""
    vpc_public_subnet_ids       = ""
    workflow_runners_table_arn  = ""
    workflow_runners_table_name = ""
  }
}

data "terraform_remote_state" "ecr" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "ecr/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "archive_file" "lambda" {
  type = "zip"
  source {
    content  = file("${path.module}/lambda/handler.py")
    filename = "handler.py"
  }
  source {
    content  = file("${path.module}/../../../../lib/python/runner_labels/__init__.py")
    filename = "runner_labels.py"
  }
  output_path = "${path.module}/.terraform/lambda.zip"
}
