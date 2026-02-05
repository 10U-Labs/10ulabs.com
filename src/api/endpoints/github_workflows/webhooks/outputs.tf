output "lambda_function_arn" {
  value = aws_lambda_function.runners_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.runners_handler.function_name
}

output "vpc_id" {
  value = data.terraform_remote_state.api_common_networking.outputs.vpc_id
}

output "public_subnets_ids" {
  value = data.terraform_remote_state.api_common_networking.outputs.public_subnets_ids
}

output "security_group_id_for_runners" {
  value = data.terraform_remote_state.api_common_networking.outputs.security_group_id_for_runners
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

output "ecr_repository_arn" {
  value = data.terraform_remote_state.api_common_docker_repository.outputs.ecr_repository_arn
}

output "ecr_repository_name" {
  value = data.terraform_remote_state.api_common_docker_repository.outputs.ecr_repository_name
}

output "ecr_repository_uri" {
  value = data.terraform_remote_state.api_common_docker_repository.outputs.ecr_repository_url
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}
