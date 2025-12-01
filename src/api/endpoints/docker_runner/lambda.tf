resource "aws_lambda_function" "handler" {
  filename         = data.archive_file.lambda.output_path
  function_name    = local.lambda_function_name
  handler          = local.lambda_handler
  role             = aws_iam_role.lambda_execution.arn
  runtime          = local.lambda_runtime
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = local.lambda_timeout
  memory_size      = local.lambda_memory_size

  environment {
    variables = {
      CONTAINER_NAME           = data.terraform_remote_state.runners.outputs.container_name
      ECR_REPOSITORY           = data.terraform_remote_state.runners.outputs.ecr_repository_name
      ECS_CLUSTER              = data.terraform_remote_state.runners.outputs.cluster_name
      GITHUB_TOKEN_SECRET_NAME = data.terraform_remote_state.runners.outputs.github_token_secret_name
      IMAGE_API_ENDPOINT       = data.terraform_remote_state.runners.outputs.api_endpoint
      SECURITY_GROUPS          = data.terraform_remote_state.runners.outputs.runner_security_group_id
      SUBNETS                  = data.terraform_remote_state.runners.outputs.vpc_public_subnet_ids
      TASK_DEFINITION          = data.terraform_remote_state.runners.outputs.task_definition_arn
      VPC_ID                   = data.terraform_remote_state.runners.outputs.vpc_id
      WORKFLOW_RUNNERS_TABLE   = data.terraform_remote_state.runners.outputs.workflow_runners_table_name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda
  ]
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 14
}
