output "lambda_function_arn" {
  value = aws_lambda_function.diagnostics_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.diagnostics_handler.function_name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.diagnostics_handler.name
}
