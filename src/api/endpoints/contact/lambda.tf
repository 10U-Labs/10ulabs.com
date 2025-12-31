data "archive_file" "contact_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/contact_handler.zip"
}

resource "aws_lambda_function" "contact_handler" {
  filename         = data.archive_file.contact_handler.output_path
  function_name    = module.shared.lambda_handler_names.contact
  role             = aws_iam_role.lambda_contact_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.contact_handler.output_base64sha256
  runtime          = "python3.13"
  architectures    = ["arm64"]
  timeout          = 10
  description      = "Contact form handler for 10U Labs website"

  environment {
    variables = {
      CONTACT_EMAIL                   = "contact@${local.domain_name}"
      RECAPTCHA_SECRET_PARAMETER_NAME = aws_ssm_parameter.recaptcha_secret.name
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.contact_handler.name
  }

  tags = merge(local.common_tags, {
    Name = module.shared.lambda_handler_names.contact
  })

  depends_on = [
    aws_iam_role_policy_attachment.lambda_contact_handler_basic,
    aws_iam_role_policy.lambda_contact_handler_ssm,
    aws_iam_role_policy.lambda_contact_handler_kms,
    aws_iam_role_policy.lambda_contact_handler_ses,
  ]

  # Force Lambda replacement when IAM role is recreated to refresh KMS grant
  lifecycle {
    replace_triggered_by = [aws_iam_role.lambda_contact_handler.id]
  }
}

resource "aws_cloudwatch_log_group" "contact_handler" {
  name              = "/aws/lambda/${module.shared.lambda_handler_names.contact}"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${module.shared.lambda_handler_names.contact}Logs"
  })
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.contact_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:${data.terraform_remote_state.api.outputs.api_gateway_id}/*"
}
