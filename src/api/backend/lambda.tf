data "archive_file" "catchall_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/catchall.py"
  output_path = "${path.module}/.terraform/lambda_packages/catchall_handler.zip"
}

resource "aws_lambda_function" "catchall_handler" {
  filename         = data.archive_file.catchall_handler.output_path
  function_name    = module.shared.lambda_handler_names.catchall
  role             = aws_iam_role.lambda_catchall_handler.arn
  handler          = "catchall.handler"
  source_code_hash = data.archive_file.catchall_handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  description      = "Catch-all handler for undefined routes"


  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.catchall_handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.catchall
  })
}

resource "aws_cloudwatch_log_group" "catchall_handler" {
  name              = var.catchall_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.catchall}Logs"
  })
}
