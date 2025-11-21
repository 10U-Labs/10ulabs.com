resource "aws_sqs_queue" "webhook_dlq" {
  name                       = "${var.lambda_function_name}-dlq"
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300

  tags = {
    Name = "${var.lambda_function_name}-dlq"
  }
}

resource "aws_sqs_queue" "job_queue_dlq" {
  name                      = "${var.lambda_function_name}-job-dlq"
  message_retention_seconds = 1209600

  tags = {
    Name = "${var.lambda_function_name}-job-dlq"
  }
}

resource "aws_sqs_queue" "job_queue" {
  name                       = "${var.lambda_function_name}-jobs"
  visibility_timeout_seconds = var.lambda_timeout_seconds * 6

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.job_queue_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name = "${var.lambda_function_name}-jobs"
  }
}

resource "aws_dynamodb_table" "idempotency" {
  name         = "${var.lambda_function_name}-idempotency"
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
    Name = "${var.lambda_function_name}-idempotency"
  }
}
