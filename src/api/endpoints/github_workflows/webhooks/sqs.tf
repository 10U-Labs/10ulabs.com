resource "aws_sqs_queue" "webhook_dlq" {
  name                       = local.webhook_dlq_name
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  tags = merge(local.common_tags, {
    Name = local.webhook_dlq_name
  })
}
