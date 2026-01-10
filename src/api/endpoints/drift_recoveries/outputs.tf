output "function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "queue_url" {
  description = "URL of the SQS queue"
  value       = aws_sqs_queue.handler.url
}

output "queue_arn" {
  description = "ARN of the SQS queue"
  value       = aws_sqs_queue.handler.arn
}

output "dlq_url" {
  description = "URL of the dead letter queue"
  value       = aws_sqs_queue.handler_dlq.url
}

output "dlq_arn" {
  description = "ARN of the dead letter queue"
  value       = aws_sqs_queue.handler_dlq.arn
}

output "config_rule_name" {
  description = "Name of the AWS Config rule"
  value       = aws_config_config_rule.required_tags.name
}

output "config_bucket_name" {
  description = "Name of the S3 bucket for Config snapshots"
  value       = aws_s3_bucket.config_bucket.id
}
