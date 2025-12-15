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

output "scanner_lambda_arn" {
  description = "ARN of the scanner Lambda"
  value       = aws_lambda_function.scanner.arn
}

output "invoker_lambda_arn" {
  description = "ARN of the invoker Lambda"
  value       = aws_lambda_function.invoker.arn
}

# SQS Queue Outputs (for API Gateway integration)
output "webhook_ingress_queue_url" {
  description = "URL of the webhook ingress SQS queue"
  value       = aws_sqs_queue.webhook_ingress.url
}

output "webhook_ingress_queue_arn" {
  description = "ARN of the webhook ingress SQS queue"
  value       = aws_sqs_queue.webhook_ingress.arn
}

output "invoker_ingress_queue_url" {
  description = "URL of the invoker ingress SQS queue"
  value       = aws_sqs_queue.invoker_ingress.url
}

output "invoker_ingress_queue_arn" {
  description = "ARN of the invoker ingress SQS queue"
  value       = aws_sqs_queue.invoker_ingress.arn
}
