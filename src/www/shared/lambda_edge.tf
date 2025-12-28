# Lambda@Edge for SPA routing
# Must be deployed in us-east-1 for CloudFront integration

data "archive_file" "spa_routing" {
  type        = "zip"
  source_file = "${path.module}/lambda/spa_routing.py"
  output_path = "${path.module}/.terraform/lambda_packages/spa_routing.zip"
}

resource "aws_iam_role" "spa_routing" {
  provider = aws.us-east-1
  name     = "${local.resource_prefix}SpaRoutingRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = [
          "lambda.amazonaws.com",
          "edgelambda.amazonaws.com"
        ]
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}SpaRoutingRole"
  })
}

resource "aws_iam_role_policy_attachment" "spa_routing_basic" {
  provider   = aws.us-east-1
  role       = aws_iam_role.spa_routing.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "spa_routing" {
  provider          = aws.us-east-1
  name              = "/aws/lambda/us-east-1.${local.resource_prefix}SpaRouting"
  retention_in_days = 7

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}SpaRoutingLogs"
  })
}

resource "aws_lambda_function" "spa_routing" {
  provider         = aws.us-east-1
  filename         = data.archive_file.spa_routing.output_path
  function_name    = "${local.resource_prefix}SpaRouting"
  role             = aws_iam_role.spa_routing.arn
  handler          = "spa_routing.handler"
  source_code_hash = data.archive_file.spa_routing.output_base64sha256
  runtime          = "python3.12"
  timeout          = 5
  memory_size      = 128
  publish          = true
  description      = "Lambda@Edge handler for SPA routing and apex-to-www redirect"

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.spa_routing.name
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}SpaRouting"
  })

  lifecycle {
    replace_triggered_by = [aws_iam_role.spa_routing.id]
  }
}
