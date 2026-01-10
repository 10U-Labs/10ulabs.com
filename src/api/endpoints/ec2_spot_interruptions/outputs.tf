output "lambda_function_arn" {
  description = "ARN of the EC2 spot interruptions Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  description = "Name of the EC2 spot interruptions Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "sqs_queue_url" {
  description = "URL of the SQS queue for EC2 spot interruption events"
  value       = aws_sqs_queue.main.url
}

output "sqs_queue_arn" {
  description = "ARN of the SQS queue for EC2 spot interruption events"
  value       = aws_sqs_queue.main.arn
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for EC2 spot interruptions"
  value       = aws_cloudwatch_event_rule.spot_interruption.arn
}
