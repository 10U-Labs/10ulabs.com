output "lambda_function_arn" {
  description = "ARN of the runners cleanup Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  description = "Name of the runners cleanup Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "sqs_queue_url" {
  description = "URL of the SQS queue for cleanup triggers"
  value       = aws_sqs_queue.main.url
}

output "sqs_queue_arn" {
  description = "ARN of the SQS queue for cleanup triggers"
  value       = aws_sqs_queue.main.arn
}

output "schedule_arn" {
  description = "ARN of the EventBridge schedule"
  value       = aws_scheduler_schedule.cleanup.arn
}
