# SQS queue for API Gateway triggers
# API Gateway can send requests to this queue, which triggers the Lambda

resource "aws_sqs_queue" "dlq" {
  name                      = local.dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.dlq_name
  })
}

resource "aws_sqs_queue" "main" {
  name                       = local.queue_name
  visibility_timeout_seconds = 600   # 10 minutes (Lambda timeout * 2)
  message_retention_seconds  = 28800 # 8 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.queue_name
  })
}
