output "lambda_function_arn" {
  value = aws_lambda_function.contact_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.contact_handler.function_name
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_contact_handler.name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.contact_handler.name
}
