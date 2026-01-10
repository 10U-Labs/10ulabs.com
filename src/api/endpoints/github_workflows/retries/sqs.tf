# SQS queue for workflow retry requests
# This queue receives requests from ec2-spot-interruptions and ecs-task-stops endpoints

resource "aws_sqs_queue" "dlq" {
  name                      = local.dlq_name
  message_retention_seconds = 1209600 # 14 days

  tags = merge(local.common_tags, {
    Name = local.dlq_name
  })
}

resource "aws_sqs_queue" "main" {
  name                       = local.queue_name
  visibility_timeout_seconds = 300   # 5 minutes (Lambda timeout * 5)
  message_retention_seconds  = 28800 # 8 hours

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(local.common_tags, {
    Name = local.queue_name
  })
}

# Policy to allow other Lambda functions to send messages to this queue
resource "aws_sqs_queue_policy" "lambda" {
  queue_url = aws_sqs_queue.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.main.arn
      Condition = {
        ArnLike = {
          "aws:SourceArn" = "arn:aws:lambda:${local.aws_region}:${local.aws_account_id}:function:*"
        }
      }
    }]
  })
}
