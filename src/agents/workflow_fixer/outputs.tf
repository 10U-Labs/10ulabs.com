output "ecr_repository_url" {
  description = "The URL of the ECR repository for the agent container"
  value       = data.terraform_remote_state.bootstrap.outputs.ecr_repository_url
}

output "agent_runtime_arn" {
  description = "The ARN of the AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.workflow_fixer.agent_runtime_arn
}

output "webhook_lambda_function_arn" {
  description = "The ARN of the webhook Lambda function"
  value       = aws_lambda_function.webhook.arn
}

output "webhook_function_url" {
  description = "The URL to invoke the webhook (for GitHub webhook)"
  value       = aws_lambda_function_url.webhook.function_url
}
