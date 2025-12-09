# ECR Repository Outputs
output "ecr_repository_arn" {
  description = "ARN of the agents ECR repository"
  value       = aws_ecr_repository.agents.arn
}

output "ecr_repository_name" {
  description = "Name of the agents ECR repository"
  value       = aws_ecr_repository.agents.name
}

output "ecr_repository_url" {
  description = "URL of the agents ECR repository"
  value       = aws_ecr_repository.agents.repository_url
}

# AgentCore Outputs
output "agentcore_execution_role_arn" {
  description = "ARN of the shared AgentCore execution role"
  value       = aws_iam_role.agentcore_execution.arn
}

output "agentcore_execution_role_name" {
  description = "Name of the shared AgentCore execution role"
  value       = aws_iam_role.agentcore_execution.name
}

# Lambda Layer Outputs
output "lambda_layer_github_auth_arn" {
  description = "ARN of the GitHub Auth Lambda layer"
  value       = aws_lambda_layer_version.github_auth.arn
}
