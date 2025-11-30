output "lambda_function_arn" {
  value = aws_lambda_function.health_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.health_handler.function_name
}
