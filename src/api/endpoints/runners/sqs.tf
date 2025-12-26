# Dead letter queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name                      = local.queue_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.queue_dlq_name
  })
}

# Main queue - receives runner requests from API Gateway
resource "aws_sqs_queue" "main" {
  name                       = local.queue_name
  visibility_timeout_seconds = local.lambda_timeout * 6
  message_retention_seconds  = 14400 # 4 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.queue_name
  })
}

# Policy to allow API Gateway to send messages to the queue
resource "aws_sqs_queue_policy" "api_gateway" {
  queue_url = aws_sqs_queue.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.main.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:*/*/POST/v1/runners"
        }
      }
    }]
  })
}
