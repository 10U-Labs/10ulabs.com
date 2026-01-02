output "lambda_function_arn" {
  value = aws_lambda_function.handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.handler.function_name
}

output "lambda_invoke_arn" {
  value = aws_lambda_function.handler.invoke_arn
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.configurations.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.configurations.arn
}
