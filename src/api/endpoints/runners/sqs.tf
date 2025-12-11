resource "aws_sqs_queue" "webhook_dlq" {
  name                       = local.webhook_dlq_name
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  tags = merge(local.common_tags, {
    Name = local.webhook_dlq_name
  })
}

resource "aws_sqs_queue" "job_queue_dlq" {
  name                      = local.job_queue_dlq_name
  message_retention_seconds = 1209600

  tags = merge(local.common_tags, {
    Name = local.job_queue_dlq_name
  })
}

resource "aws_sqs_queue" "job_queue" {
  name                       = local.job_queue_name
  visibility_timeout_seconds = local.lambda_timeout_seconds * 6

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.job_queue_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.job_queue_name
  })
}

resource "aws_sqs_queue" "drift_recovery" {
  name                        = "${local.resource_prefix}-DriftRecovery.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  deduplication_scope         = "queue"
  fifo_throughput_limit       = "perQueue"
  message_retention_seconds   = 300
  visibility_timeout_seconds  = 60

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-DriftRecovery-Queue"
  })
}

resource "aws_sqs_queue_policy" "drift_recovery" {
  queue_url = aws_sqs_queue.drift_recovery.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "events.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.drift_recovery.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_cloudwatch_event_rule.config_compliance_change.arn
        }
      }
    }]
  })
}
