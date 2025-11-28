resource "aws_ses_email_identity" "contact" {
  email = "contact@${local.domain_name}"
}

data "archive_file" "contact_handler" {
  type        = "zip"
  source_file = "${path.module}/lambdas/contact.py"
  output_path = "${path.module}/.terraform/lambda_packages/contact_handler.zip"
}

resource "aws_iam_role" "contact_lambda" {
  name = "${local.resource_prefix}ContactLambdaRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}ContactLambdaRole"
  })
}

resource "aws_iam_role_policy_attachment" "contact_lambda_basic" {
  role       = aws_iam_role.contact_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "contact_lambda_ses" {
  name = "SESAccess"
  role = aws_iam_role.contact_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["ses:SendEmail"]
      Resource = ["*"]
      Condition = {
        StringEquals = {
          "ses:FromAddress" = "contact@${local.domain_name}"
        }
      }
    }]
  })
}

resource "aws_cloudwatch_log_group" "contact_handler" {
  name              = "/aws/lambda/${local.resource_prefix}ContactHandler"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}ContactHandler-logs"
  })
}

resource "aws_lambda_function" "contact_handler" {
  filename         = data.archive_file.contact_handler.output_path
  function_name    = "${local.resource_prefix}ContactHandler"
  role             = aws_iam_role.contact_lambda.arn
  handler          = "contact.handler"
  source_code_hash = data.archive_file.contact_handler.output_base64sha256
  runtime          = "python3.13"
  timeout          = 10
  memory_size      = 128
  description      = "Handles contact form submissions and sends emails via SES"

  environment {
    variables = {
      CONTACT_EMAIL = "contact@${local.domain_name}"
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.contact_handler.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}ContactHandler"
  })
}

resource "aws_lambda_function_url" "contact_handler" {
  function_name      = aws_lambda_function.contact_handler.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["https://${local.www_fqdn}", "https://${local.apex_fqdn}"]
    allow_methods = ["POST"]
    allow_headers = ["Content-Type"]
    max_age       = 86400
  }
}
