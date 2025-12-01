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

output "api_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/"
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "cluster_arn" {
  value = aws_ecs_cluster.runner.arn
}

output "cluster_name" {
  value = aws_ecs_cluster.runner.name
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

output "ec2_spot_instance_types" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_spot_instance_types
}

output "ecr_repository_arn" {
  value = data.terraform_remote_state.ecr.outputs.repository_arn
}

output "ecr_repository_name" {
  value = data.terraform_remote_state.ecr.outputs.repository_name
}

output "ecr_repository_uri" {
  value = data.terraform_remote_state.ecr.outputs.repository_url
}

output "execution_role_arn" {
  value = aws_iam_role.ecs_execution_role.arn
}

output "fargate_cpu_architecture" {
  value = var.fargate_cpu_architecture
}

output "github_token_secret_name" {
  value = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
}

output "runner_security_group_id" {
  value = aws_security_group.runner_sg.id
}

output "ssm_parameter_name_for_latest_ami" {
  value = aws_ssm_parameter.latest_ami.name
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.runner.arn
}

output "task_role_arn" {
  value = aws_iam_role.ecs_task_role.arn
}

output "vpc_id" {
  value = aws_vpc.runner_vpc.id
}

output "vpc_public_subnet_ids" {
  value = join(",", aws_subnet.public[*].id)
}

output "webhook_parameter_arn" {
  value = aws_ssm_parameter.webhook_secret.arn
}

output "webhook_parameter_name" {
  value = aws_ssm_parameter.webhook_secret.name
}

output "workflow_runners_table_arn" {
  value = aws_dynamodb_table.workflow_runners.arn
}

output "workflow_runners_table_name" {
  value = aws_dynamodb_table.workflow_runners.name
}

output "api_key_ssm_parameter_arn" {
  value = aws_ssm_parameter.api_key.arn
}

output "ec2_max_spot_price" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_max_spot_price
}

output "ec2_runner_managed_by_tag" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_managed_by_tag
}

output "ec2_runner_role_arn" {
  value = data.terraform_remote_state.ec2_runner.outputs.ec2_runner_role_arn
}

output "container_name" {
  value = var.container_name
}
