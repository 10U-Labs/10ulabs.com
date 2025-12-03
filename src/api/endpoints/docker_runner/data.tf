data "terraform_remote_state" "runners" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "runners/terraform.tfstate"
    region = module.shared.aws_region
  }

  defaults = {
    api_endpoint                = ""
    cluster_arn                 = ""
    cluster_name                = ""
    container_name              = ""
    ecr_repository_name         = ""
    execution_role_arn          = ""
    github_token_secret_name    = ""
    runner_security_group_id    = ""
    task_definition_arn         = ""
    task_role_arn               = ""
    vpc_id                      = ""
    vpc_public_subnet_ids       = ""
    workflow_runners_table_arn  = ""
    workflow_runners_table_name = ""
  }
}

data "terraform_remote_state" "bootstrap" {
  backend = "s3"
  config = {
    bucket = module.shared.name_for_terraform_state_bucket
    key    = "bootstrap/terraform.tfstate"
    region = module.shared.aws_region
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/.terraform/lambda.zip"
}
