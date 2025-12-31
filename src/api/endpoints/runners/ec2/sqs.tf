# SQS queue for EC2 runner requests
# This queue receives requests from /v1/runners endpoint

resource "aws_sqs_queue" "dlq" {
  name                      = "${module.common.lambda_handler_names.ec2_runner}Dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = "${module.common.lambda_handler_names.ec2_runner}Dlq"
  })
}

resource "aws_sqs_queue" "main" {
  name                       = module.common.lambda_handler_names.ec2_runner
  visibility_timeout_seconds = 300   # 5 minutes (Lambda timeout * 5)
  message_retention_seconds  = 28800 # 8 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = module.common.lambda_handler_names.ec2_runner
  })
}

# Policy to allow API Gateway to send messages to this queue
resource "aws_sqs_queue_policy" "api_gateway" {
  queue_url = aws_sqs_queue.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.main.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:aws:execute-api:${local.aws_region}:${local.aws_account_id}:*/*/POST/v1/runners/ec2"
        }
      }
    }]
  })
}
