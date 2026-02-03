# Note: webhook_ingress queue removed - API Gateway now invokes Lambda directly (AWS_PROXY)
# Note: ignored_events queue removed - archive logic merged into webhook_router (direct S3 writes)

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
