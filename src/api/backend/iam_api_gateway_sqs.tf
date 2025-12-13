# IAM role for API Gateway to send messages to SQS (used for direct SQS integration)
# This removes Lambda from the API Gateway hot path, preventing throttling from causing 500 errors

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

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:GetQueueUrl"
      ]
      Resource = data.terraform_remote_state.runners.outputs.webhook_ingress_queue_arn
    }]
  })
}
