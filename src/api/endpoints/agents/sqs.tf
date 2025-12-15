# SQS Queues for Agent Lambdas
#
# All Lambdas are protected by SQS - defensive architecture regardless of trigger source.
# Following the runners endpoint pattern for durability and buffering.

locals {
  # SQS naming
  webhook_queue_name = "${local.resource_prefix}-webhook-ingress"
  scanner_queue_name = "${local.resource_prefix}-scanner"
  invoker_queue_name = "${local.resource_prefix}-invoker-ingress"

  # Common SQS settings
  visibility_timeout = 720 # 6 × Lambda timeout (120s)
  max_receive_count  = 3
  dlq_retention      = 1209600 # 14 days
}

# =============================================================================
# Webhook Ingress Queue (GitHub webhooks -> webhook.py)
# =============================================================================

resource "aws_sqs_queue" "webhook_ingress" {
  name                       = local.webhook_queue_name
  message_retention_seconds  = 3600 # 1 hour (DDoS protection)
  visibility_timeout_seconds = local.visibility_timeout
  receive_wait_time_seconds  = 20 # Long polling

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.webhook_dlq.arn
    maxReceiveCount     = local.max_receive_count
  })

  tags = merge(local.common_tags, {
    Name = local.webhook_queue_name
  })
}

resource "aws_sqs_queue" "webhook_dlq" {
  name                      = "${local.webhook_queue_name}-dlq"
  message_retention_seconds = local.dlq_retention

  tags = merge(local.common_tags, {
    Name = "${local.webhook_queue_name}-dlq"
  })
}

# =============================================================================
# Scanner Queue (EventBridge -> scanner.py)
# =============================================================================

resource "aws_sqs_queue" "scanner" {
  name                       = local.scanner_queue_name
  message_retention_seconds  = 3600 # 1 hour
  visibility_timeout_seconds = local.visibility_timeout
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.scanner_dlq.arn
    maxReceiveCount     = local.max_receive_count
  })

  tags = merge(local.common_tags, {
    Name = local.scanner_queue_name
  })
}

resource "aws_sqs_queue" "scanner_dlq" {
  name                      = "${local.scanner_queue_name}-dlq"
  message_retention_seconds = local.dlq_retention

  tags = merge(local.common_tags, {
    Name = "${local.scanner_queue_name}-dlq"
  })
}

# =============================================================================
# Invoker Ingress Queue (Direct API calls -> invoker.py)
# =============================================================================

resource "aws_sqs_queue" "invoker_ingress" {
  name                       = local.invoker_queue_name
  message_retention_seconds  = 86400 # 24 hours
  visibility_timeout_seconds = local.visibility_timeout
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.invoker_dlq.arn
    maxReceiveCount     = local.max_receive_count
  })

  tags = merge(local.common_tags, {
    Name = local.invoker_queue_name
  })
}

resource "aws_sqs_queue" "invoker_dlq" {
  name                      = "${local.invoker_queue_name}-dlq"
  message_retention_seconds = local.dlq_retention

  tags = merge(local.common_tags, {
    Name = "${local.invoker_queue_name}-dlq"
  })
}

# =============================================================================
# EventBridge -> Scanner SQS
# =============================================================================

resource "aws_cloudwatch_event_rule" "scheduled_scan" {
  name                = "${local.resource_prefix}-scheduled-scan"
  description         = "Trigger agent to scan for unresolved workflow failures"
  schedule_expression = "rate(15 minutes)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "scheduled_scan_sqs" {
  rule      = aws_cloudwatch_event_rule.scheduled_scan.name
  target_id = "ScannerQueue"
  arn       = aws_sqs_queue.scanner.arn
}

resource "aws_sqs_queue_policy" "scanner_eventbridge" {
  queue_url = aws_sqs_queue.scanner.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowEventBridgeSendMessage"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.scanner.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_cloudwatch_event_rule.scheduled_scan.arn
          }
        }
      }
    ]
  })
}
