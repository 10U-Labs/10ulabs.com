# IAM role for API Gateway to send messages to SQS (used for direct SQS integration)
# This removes Lambda from the API Gateway hot path, preventing throttling from causing 500 errors
# ARN constructed from known values to avoid dependency on runners remote state
# Queue: ${handler}Ingress where handler = module.shared.lambda_handler_names.webhook

resource "aws_iam_role" "api_gateway_sqs" {
  name = "${local.resource_prefix}ApiGatewaySqsRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}ApiGatewaySqsRole"
  })
}

resource "aws_iam_role_policy" "api_gateway_sqs" {
  name = "SendToWebhookIngressQueue"
  role = aws_iam_role.api_gateway_sqs.id

  # Construct ARN from known values (avoid dependency on runners remote state)
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:GetQueueUrl"
      ]
      Resource = "arn:aws:sqs:${local.aws_region}:${local.aws_account_id}:${local.webhook_ingress_queue_name}"
    }]
  })
}
