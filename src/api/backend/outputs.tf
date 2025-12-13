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

output "ec2_runner_ami_purpose_value" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_ami_purpose_value
}

output "ec2_runner_ami_stable_tag" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_ami_stable_tag
}

output "ec2_instance_types" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_instance_types
}

output "runner_security_group_id" {
  value = data.terraform_remote_state.runners.outputs.runner_security_group_id
}

output "ssm_parameter_name_for_latest_ami" {
  value = data.terraform_remote_state.runners.outputs.ssm_parameter_name_for_latest_ami
}

output "vpc_public_subnet_ids" {
  value = data.terraform_remote_state.runners.outputs.vpc_public_subnet_ids
}

output "vpc_id" {
  value = data.terraform_remote_state.runners.outputs.vpc_id
}

# Audit infrastructure outputs
output "api_audit_log_table_name" {
  value = aws_dynamodb_table.api_audit_log.name
}

output "api_audit_log_table_arn" {
  value = aws_dynamodb_table.api_audit_log.arn
}
