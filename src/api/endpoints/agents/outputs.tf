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

# Lambda Layer Outputs
output "lambda_layer_github_auth_arn" {
  description = "ARN of the GitHub Auth Lambda layer"
  value       = aws_lambda_layer_version.github_auth.arn
}

# AgentCore Outputs
output "agentcore_runtime_arn" {
  description = "ARN of the AgentCore runtime"
  value       = aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn
}

output "agentcore_execution_role_arn" {
  description = "ARN of the AgentCore execution role"
  value       = aws_iam_role.agentcore_execution.arn
}

# Lambda Outputs
output "webhook_lambda_arn" {
  description = "ARN of the webhook Lambda"
  value       = aws_lambda_function.webhook.arn
}

output "webhook_lambda_url" {
  description = "Function URL of the webhook Lambda"
  value       = aws_lambda_function_url.webhook.function_url
}
