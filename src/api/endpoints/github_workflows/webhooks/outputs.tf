output "lambda_function_arn" {
  value = aws_lambda_function.runners_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.runners_handler.function_name
}

output "github_token_secret_name" {
  value = module.common.ssm_github_pat_name
}

output "webhook_parameter_name" {
  value = aws_ssm_parameter.webhook_secret.name
}

output "webhook_parameter_arn" {
  value = aws_ssm_parameter.webhook_secret.arn
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}
