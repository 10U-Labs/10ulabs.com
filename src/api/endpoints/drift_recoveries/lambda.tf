data "archive_file" "handler" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "handler" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.13"
  architectures    = ["arm64"]
  filename         = data.archive_file.handler.output_path
  source_code_hash = data.archive_file.handler.output_base64sha256
  timeout          = 120
  memory_size      = 256

  environment {
    variables = {
      GITHUB_REPO                 = local.github_repo
      GITHUB_TOKEN_PARAMETER_NAME = module.common.ssm_github_pat_name
      SNS_TOPIC_ARN               = aws_sns_topic.alerts.arn
      MANAGED_VPC_ID              = data.terraform_remote_state.api_common_networking.outputs.vpc_id
    }
  }

  tags = merge(local.common_tags, {
    Name = local.function_name
  })
}

resource "aws_lambda_event_source_mapping" "sqs" {
  event_source_arn = aws_sqs_queue.handler.arn
  function_name    = aws_lambda_function.handler.arn
  batch_size       = 1
  enabled          = true
}

resource "aws_cloudwatch_log_group" "handler" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "${local.function_name}LogGroup"
  })
}
