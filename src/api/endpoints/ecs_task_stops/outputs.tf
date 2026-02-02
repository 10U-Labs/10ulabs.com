output "lambda_function_arn" {
  description = "ARN of the ECS task stops Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  description = "Name of the ECS task stops Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for ECS task stopped events"
  value       = aws_cloudwatch_event_rule.task_stopped.arn
}
