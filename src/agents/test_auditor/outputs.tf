output "ecr_repository_url" {
  description = "The URL of the ECR repository for the agent container"
  value       = data.terraform_remote_state.bootstrap.outputs.ecr_repository_url
}

output "agent_runtime_id" {
  description = "The ID of the AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.test_auditor.agent_runtime_id
}

output "agent_runtime_arn" {
  description = "The ARN of the AgentCore Runtime"
  value       = aws_bedrockagentcore_agent_runtime.test_auditor.arn
}

output "gateway_id" {
  description = "The ID of the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.test_auditor.gateway_id
}

output "gateway_endpoint" {
  description = "The endpoint URL for the AgentCore Gateway"
  value       = aws_bedrockagentcore_gateway.test_auditor.endpoint
}

output "lambda_function_arn" {
  description = "The ARN of the action group Lambda function"
  value       = aws_lambda_function.action_group.arn
}
