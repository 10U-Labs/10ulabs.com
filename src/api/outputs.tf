output "api_url" {
  description = "API Gateway URL"
  value       = "${aws_api_gateway_stage.prod.invoke_url}/"
}

output "api_domain_name" {
  description = "Custom domain name for API"
  value       = var.domain_subdomain
}

output "api_endpoint" {
  description = "API endpoint URL"
  value       = "https://${var.domain_subdomain}"
}

output "api_gateway_rest_api_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "vpc_id" {
  description = "VPC ID for API and GitHub self-hosted runners"
  value       = aws_vpc.runner_vpc.id
}

output "vpc_public_subnet_ids" {
  description = "Comma-separated list of public subnet IDs"
  value       = join(",", aws_subnet.public[*].id)
}

output "runner_security_group_id" {
  description = "Security group ID for runners"
  value       = aws_security_group.runner_sg.id
}

output "ecr_repository_uri" {
  description = "ECR repository URI for self-hosted runner Docker images"
  value       = aws_ecr_repository.runner.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name for self-hosted runners"
  value       = aws_ecr_repository.runner.name
}

output "cluster_name" {
  description = "ECS cluster name for GitHub self-hosted runners"
  value       = aws_ecs_cluster.runner.name
}

output "cluster_arn" {
  description = "ECS cluster ARN for GitHub self-hosted runners"
  value       = aws_ecs_cluster.runner.arn
}

output "task_definition_arn" {
  description = "Fargate task definition ARN for runners"
  value       = aws_ecs_task_definition.runner.arn
}

output "task_role_arn" {
  description = "Task role ARN for Fargate runners"
  value       = aws_iam_role.ecs_task_role.arn
}

output "execution_role_arn" {
  description = "Execution role ARN for Fargate runners"
  value       = aws_iam_role.ecs_execution_role.arn
}

output "webhook_parameter_name" {
  description = "Webhook parameter name in SSM Parameter Store"
  value       = aws_ssm_parameter.webhook_secret.name
}

output "webhook_parameter_arn" {
  description = "ARN of the webhook parameter"
  value       = aws_ssm_parameter.webhook_secret.arn
}

output "github_token_secret_name" {
  description = "GitHub token secret name in SSM Parameter Store"
  value       = var.github_token_secret_name
}

output "ec2_runner_role_name" {
  description = "EC2 runner IAM role name"
  value       = aws_iam_role.ec2_runner_role.name
}

output "ec2_instance_profile_name" {
  description = "EC2 instance profile name for runners"
  value       = aws_iam_instance_profile.ec2_runner.name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "api_key_id" {
  description = "API Gateway API Key ID"
  value       = aws_api_gateway_api_key.main.id
}

output "api_key_ssm_parameter" {
  description = "SSM Parameter name containing the API key"
  value       = aws_ssm_parameter.api_key.name
}
