output "lambda_function_arn" {
  value = aws_lambda_function.runners_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.runners_handler.function_name
}

output "vpc_id" {
  value = data.terraform_remote_state.api_shared_networking.outputs.vpc_id
}

output "vpc_public_subnet_ids" {
  value = data.terraform_remote_state.api_shared_networking.outputs.vpc_public_subnet_ids
}

output "runner_security_group_id" {
  value = data.terraform_remote_state.api_shared_networking.outputs.runner_security_group_id
}

output "workflow_runners_table_name" {
  value = aws_dynamodb_table.workflow_runners.name
}

output "workflow_runners_table_arn" {
  value = aws_dynamodb_table.workflow_runners.arn
}

output "github_token_secret_name" {
  value = module.shared.ssm_github_pat_name
}

output "webhook_parameter_name" {
  value = aws_ssm_parameter.webhook_secret.name
}

output "webhook_parameter_arn" {
  value = aws_ssm_parameter.webhook_secret.arn
}

output "ecr_repository_arn" {
  value = data.terraform_remote_state.api_shared_docker_repository.outputs.ecr_repository_arn
}

output "ecr_repository_name" {
  value = data.terraform_remote_state.api_shared_docker_repository.outputs.ecr_repository_name
}

output "ecr_repository_uri" {
  value = data.terraform_remote_state.api_shared_docker_repository.outputs.ecr_repository_url
}

output "ssm_parameter_name_for_latest_ami" {
  value = aws_ssm_parameter.latest_ami.name
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}

output "webhook_ingress_queue_url" {
  description = "URL of the webhook ingress queue for API Gateway SQS integration"
  value       = aws_sqs_queue.webhook_ingress.url
}

output "webhook_ingress_queue_arn" {
  description = "ARN of the webhook ingress queue"
  value       = aws_sqs_queue.webhook_ingress.arn
}

output "webhook_ingress_queue_name" {
  description = "Name of the webhook ingress queue"
  value       = aws_sqs_queue.webhook_ingress.name
}
