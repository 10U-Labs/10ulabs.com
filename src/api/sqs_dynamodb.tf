resource "aws_sqs_queue" "webhook_dlq" {
  name                       = var.webhook_dlq_name
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  tags = {
    Name = var.webhook_dlq_name
  }
}

resource "aws_sqs_queue" "job_queue_dlq" {
  name                      = var.job_queue_dlq_name
  message_retention_seconds = 1209600

  tags = {
    Name = var.job_queue_dlq_name
  }
}

resource "aws_sqs_queue" "job_queue" {
  name                       = var.job_queue_name
  visibility_timeout_seconds = var.lambda_timeout_seconds * 6

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.job_queue_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = var.job_queue_name
  }
}

resource "aws_dynamodb_table" "idempotency" {
  name         = var.idempotency_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"

  attribute {
    name = "request_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = var.idempotency_table_name
  }
}

resource "aws_dynamodb_table" "incidents" {
  name         = "${module.config.resource_prefix}-incidents"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "incident_id"

  attribute {
    name = "incident_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${module.config.resource_prefix}-incidents"
  }
}

resource "aws_dynamodb_table" "circuit_breaker_state" {
  name         = "${module.config.resource_prefix}-circuit-breaker-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "state_id"

  attribute {
    name = "state_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${module.config.resource_prefix}-circuit-breaker-state"
  }
}
