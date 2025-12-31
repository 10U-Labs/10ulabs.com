# Write-ahead queue module for API endpoint durability
# Creates an SQS queue with DLQ for write-ahead logging pattern

resource "aws_sqs_queue" "dlq" {
  name                      = "${var.queue_name}Dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = merge(var.tags, {
    Name = "${var.queue_name}Dlq"
  })
}

resource "aws_sqs_queue" "main" {
  name                       = var.queue_name
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(var.tags, {
    Name = var.queue_name
  })
}
