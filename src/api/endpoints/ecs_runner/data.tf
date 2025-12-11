data "terraform_remote_state" "api_shared_runners" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/runners/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "terraform_remote_state" "api_shared_ecs_runner" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "api/shared/ecs_runner/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "terraform_remote_state" "runners" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "runners/terraform.tfstate"
    region = module.shared.aws_region
  }

  defaults = {
    api_endpoint                = ""
    github_token_secret_name    = ""
    workflow_runners_table_arn  = ""
    workflow_runners_table_name = ""
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
  source {
    content  = file("${path.module}/../../../../etc/runners.json")
    filename = "etc/runners.json"
  }
  output_path = "${path.module}/.terraform/lambda.zip"
}
