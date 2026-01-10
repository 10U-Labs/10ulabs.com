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
          "aws:SourceArn" = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:*/*/POST/v1/github-workflows/webhooks"
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

# Note: job_queue and job_queue_dlq removed - routing logic moved to /v1/runners endpoint
# Note: cancellation_queue removed - runners are ephemeral and self-terminate
# Note: drift_recovery queue removed - migrated to /v1/drift-recoveries endpoint
