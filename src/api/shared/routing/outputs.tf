output "api_domain_name" {
  value = local.api_fqdn
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}

output "api_gateway_rest_api_id" {
  value = aws_api_gateway_rest_api.main.id
}

output "api_key_id" {
  value = aws_api_gateway_api_key.main.id
}

output "api_key_ssm_parameter" {
  value = aws_ssm_parameter.api_key.name
}

output "api_key_ssm_parameter_arn" {
  value = aws_ssm_parameter.api_key.arn
}

output "api_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "security_group_id_for_runners" {
  value = data.terraform_remote_state.jit_runner_requests.outputs.security_group_id_for_runners
}

output "ssm_parameter_name_for_latest_ami" {
  value = data.terraform_remote_state.jit_runner_requests.outputs.ssm_parameter_name_for_latest_ami
}

output "public_subnet_ids" {
  value = data.terraform_remote_state.jit_runner_requests.outputs.public_subnet_ids
}

output "vpc_id" {
  value = data.terraform_remote_state.jit_runner_requests.outputs.vpc_id
}

# Audit infrastructure outputs
output "api_audit_log_table_name" {
  value = aws_dynamodb_table.api_audit_log.name
}

output "api_audit_log_table_arn" {
  value = aws_dynamodb_table.api_audit_log.arn
}

# Firehose outputs for log subscriptions in other endpoints
output "firehose_cloudwatch_logs_arn" {
  description = "ARN of the CloudWatch Logs Firehose delivery stream"
  value       = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
}

output "cloudwatch_logs_firehose_role_arn" {
  description = "ARN of the IAM role for CloudWatch Logs to Firehose"
  value       = aws_iam_role.cloudwatch_logs_firehose.arn
}
