output "lambda_function_arn" {
  description = "ARN of the runners cleanup Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  description = "Name of the runners cleanup Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "schedule_arn" {
  description = "ARN of the EventBridge schedule"
  value       = aws_scheduler_schedule.cleanup.arn
}
