output "ecr_repository_url" {
  description = "The URL of the ECR repository for the agent container"
  value       = aws_ecr_repository.agent.repository_url
}

output "agent_runtime_arn" {
  description = "The ARN of the AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.agent_creator.arn
}

output "lambda_function_arn" {
  description = "The ARN of the invocation Lambda function"
  value       = aws_lambda_function.invoke.arn
}

output "lambda_function_url" {
  description = "The URL to invoke the agent"
  value       = aws_lambda_function_url.invoke.function_url
}
