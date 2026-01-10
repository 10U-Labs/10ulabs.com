output "lambda_function_arn" {
  description = "ARN of the GitHub workflows retries Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  description = "Name of the GitHub workflows retries Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "sqs_queue_url" {
  description = "URL of the SQS queue for retry requests"
  value       = aws_sqs_queue.main.url
}

output "sqs_queue_arn" {
  description = "ARN of the SQS queue for retry requests"
  value       = aws_sqs_queue.main.arn
}
