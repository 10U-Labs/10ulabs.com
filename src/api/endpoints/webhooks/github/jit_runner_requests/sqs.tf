# Webhook ingress queue - receives webhooks directly from API Gateway (no Lambda in hot path)
resource "aws_sqs_queue" "webhook_ingress_dlq" {
  name                      = local.webhook_ingress_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.webhook_ingress_dlq_name
  })
}

resource "aws_sqs_queue" "webhook_ingress" {
  name                       = local.webhook_ingress_queue_name
  visibility_timeout_seconds = local.lambda_timeout_seconds * 6
  message_retention_seconds  = 3600 # 1 hour - short retention for DDoS protection

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.webhook_ingress_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.webhook_ingress_queue_name
  })
}

# Policy to allow API Gateway to send messages to webhook_ingress queue
resource "aws_sqs_queue_policy" "webhook_ingress" {
  queue_url = aws_sqs_queue.webhook_ingress.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.webhook_ingress.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:*/*/POST/v1/webhooks/github/jit-runner-requests"
        }
      }
    }]
  })
}

# Ignored events queue - stores webhook events that don't match our handlers
resource "aws_sqs_queue" "ignored_events_dlq" {
  name                      = local.ignored_events_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.ignored_events_dlq_name
  })
}

resource "aws_sqs_queue" "ignored_events" {
  name                       = local.ignored_events_queue_name
  visibility_timeout_seconds = 300
  message_retention_seconds  = 604800 # 7 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ignored_events_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.ignored_events_queue_name
  })
}

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

# Cancellation queue - receives cancelled/completed workflow events for runner termination
resource "aws_sqs_queue" "cancellation_dlq" {
  name                      = local.cancellation_queue_dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.cancellation_queue_dlq_name
  })
}

resource "aws_sqs_queue" "cancellation" {
  name                       = local.cancellation_queue_name
  visibility_timeout_seconds = local.lambda_timeout_seconds * 6

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.cancellation_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.cancellation_queue_name
  })
}

resource "aws_sqs_queue" "drift_recovery" {
  name                        = "${local.resource_prefix}DriftRecovery.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  deduplication_scope         = "queue"
  fifo_throughput_limit       = "perQueue"
  message_retention_seconds   = 300
  visibility_timeout_seconds  = 60

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}DriftRecoveryQueue"
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
