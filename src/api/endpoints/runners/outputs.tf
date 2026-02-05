output "lambda_function_name" {
  description = "Name of the runners router Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "lambda_function_arn" {
  description = "ARN of the runners router Lambda function"
  value       = aws_lambda_function.handler.arn
}
