output "lambda_function_arn" {
  value = aws_lambda_function.runners_handler.arn
}

output "lambda_function_name" {
  value = aws_lambda_function.runners_handler.function_name
}

output "vpc_id" {
  value = data.terraform_remote_state.bootstrap.outputs.vpc_id
}

output "vpc_public_subnet_ids" {
  value = data.terraform_remote_state.bootstrap.outputs.vpc_public_subnet_ids
}

output "runner_security_group_id" {
  value = data.terraform_remote_state.bootstrap.outputs.runner_security_group_id
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
  value = data.terraform_remote_state.bootstrap.outputs.ecr_runners_repository_arn
}

output "ecr_repository_name" {
  value = data.terraform_remote_state.bootstrap.outputs.ecr_runners_repository_name
}

output "ecr_repository_uri" {
  value = data.terraform_remote_state.bootstrap.outputs.ecr_runners_repository_url
}

output "ec2_instance_profile_name" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_instance_profile_name
}

output "ec2_runner_ami_purpose_tag" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_ami_purpose_tag
}

output "ec2_runner_ami_purpose_value" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_ami_purpose_value
}

output "ec2_runner_ami_stable_tag" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_ami_stable_tag
}

output "ec2_runner_role_name" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_role_name
}

output "ec2_instance_types" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_instance_types
}

output "ec2_runner_managed_by_tag" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag
}

output "ec2_runner_role_arn" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_role_arn
}

output "ssm_parameter_name_for_latest_ami" {
  value = aws_ssm_parameter.latest_ami.name
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}
