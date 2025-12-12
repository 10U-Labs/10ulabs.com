data "archive_file" "simulation_soc_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/simulation_soc_handler.zip"
}

resource "aws_lambda_function" "simulation_soc_handler" {
  filename         = data.archive_file.simulation_soc_handler.output_path
  function_name    = module.shared.lambda_handler_names.simulation_soc
  role             = aws_iam_role.lambda_simulation_soc_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.simulation_soc_handler.output_base64sha256
  runtime          = "python3.11"
  architectures    = ["arm64"]
  timeout          = 10
  description      = "Tri-mode SoC simulation endpoint for API"

  environment {
    variables = {
      GOOGLE_CLIENT_ID = var.google_client_id
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.simulation_soc_handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.simulation_soc
  })

  depends_on = [
    aws_iam_role_policy_attachment.lambda_simulation_soc_handler_basic,
    aws_iam_role_policy.lambda_simulation_soc_handler_kms,
  ]
}

# Generate frontend auth config
resource "local_file" "auth_config" {
  content  = "var GOOGLE_CLIENT_ID = '${var.google_client_id}';\n"
  filename = "${path.module}/../../../www/paths/simulations/soc/js/config.js"
}

resource "aws_cloudwatch_log_group" "simulation_soc_handler" {
  name              = local.handler_log_group
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.simulation_soc}Logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.simulation_soc_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_rest_api_id}/*"
}
