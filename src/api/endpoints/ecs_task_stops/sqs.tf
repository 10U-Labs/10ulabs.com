# SQS queue for ECS task stopped events
# EventBridge sends events to this queue, which triggers the Lambda

resource "aws_sqs_queue" "dlq" {
  name                      = local.dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.dlq_name
  })
}

resource "aws_sqs_queue" "main" {
  name                       = local.queue_name
  visibility_timeout_seconds = 300   # 5 minutes (Lambda timeout * 5)
  message_retention_seconds  = 28800 # 8 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.queue_name
  })
}

# Policy to allow EventBridge to send messages to the queue
resource "aws_sqs_queue_policy" "eventbridge" {
  queue_url = aws_sqs_queue.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.main.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.task_stopped.arn
        }
      }
    }]
  })
}
