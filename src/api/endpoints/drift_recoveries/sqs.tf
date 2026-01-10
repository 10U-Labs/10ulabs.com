resource "aws_sqs_queue" "handler" {
  name                        = "${local.queue_name}.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  deduplication_scope         = "queue"
  fifo_throughput_limit       = "perQueue"
  visibility_timeout_seconds  = 300
  message_retention_seconds   = 86400

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.handler_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = "${local.queue_name}Queue"
  })
}

resource "aws_sqs_queue" "handler_dlq" {
  name                       = "${local.queue_name}DLQ.fifo"
  fifo_queue                 = true
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  tags = merge(local.common_tags, {
    Name = "${local.queue_name}DLQ"
  })
}

resource "aws_sqs_queue_policy" "handler" {
  queue_url = aws_sqs_queue.handler.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.handler.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.config_compliance_change.arn
        }
      }
    }]
  })
}

resource "aws_sqs_queue_redrive_allow_policy" "handler_dlq" {
  queue_url = aws_sqs_queue.handler_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.handler.arn]
  })
}
