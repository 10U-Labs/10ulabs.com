data "archive_file" "simulation_soc_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/simulation_soc_handler.zip"
}

resource "aws_lambda_function" "simulation_soc_handler" {
  filename         = data.archive_file.simulation_soc_handler.output_path
  function_name    = var.simulation_soc_handler_function_name
  role             = aws_iam_role.lambda_simulation_soc_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.simulation_soc_handler.output_base64sha256
  runtime          = "python3.11"
  timeout          = 10
  description      = "Tri-mode SoC simulation endpoint for API"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.simulation_soc_handler.name
  }

  tags = merge(local.common_tags, {
    Name = var.simulation_soc_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "simulation_soc_handler" {
  name              = var.simulation_soc_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.simulation_soc_handler_function_name}-logs"
  })
}
