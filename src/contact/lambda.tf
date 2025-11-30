data "archive_file" "contact_handler" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/.terraform/lambda_packages/contact_handler.zip"
}

resource "aws_lambda_function" "contact_handler" {
  filename         = data.archive_file.contact_handler.output_path
  function_name    = var.contact_handler_function_name
  role             = aws_iam_role.lambda_contact_handler.arn
  handler          = "handler.handler"
  source_code_hash = data.archive_file.contact_handler.output_base64sha256
  runtime          = "python3.13"
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
    Name = var.contact_handler_function_name
  })
}

resource "aws_cloudwatch_log_group" "contact_handler" {
  name              = var.contact_handler_log_group_name
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${var.contact_handler_function_name}-logs"
  })
}
