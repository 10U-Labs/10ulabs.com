output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.handler.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.handler.arn
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB events table"
  value       = aws_dynamodb_table.events.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB events table"
  value       = aws_dynamodb_table.events.arn
}
