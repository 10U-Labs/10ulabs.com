output "api_url" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/"
}

output "api_domain_name" {
  value = local.api_fqdn
}

output "api_endpoint" {
  value = "https://${local.api_fqdn}"
}

output "api_gateway_rest_api_id" {
  value = aws_api_gateway_rest_api.main.id
}

output "vpc_id" {
  value = aws_vpc.runner_vpc.id
}

output "vpc_public_subnet_ids" {
  value = join(",", aws_subnet.public[*].id)
}

output "runner_security_group_id" {
  value = aws_security_group.runner_sg.id
}

output "ecr_repository_uri" {
  value = aws_ecr_repository.runner.repository_url
}

output "ecr_repository_name" {
  value = aws_ecr_repository.runner.name
}

output "cluster_name" {
  value = aws_ecs_cluster.runner.name
}

output "cluster_arn" {
  value = aws_ecs_cluster.runner.arn
}

output "task_definition_arn" {
  value = aws_ecs_task_definition.runner.arn
}

output "task_role_arn" {
  value = aws_iam_role.ecs_task_role.arn
}

output "execution_role_arn" {
  value = aws_iam_role.ecs_execution_role.arn
}

output "webhook_parameter_name" {
  value = aws_ssm_parameter.webhook_secret.name
}

output "webhook_parameter_arn" {
  value = aws_ssm_parameter.webhook_secret.arn
}

output "github_token_secret_name" {
  value = data.terraform_remote_state.bootstrap.outputs.ssm_parameter_name_for_github_pat
}

output "ec2_runner_role_name" {
  value = aws_iam_role.ec2_runner_role.name
}

output "ec2_instance_profile_name" {
  value = aws_iam_instance_profile.ec2_runner.name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "api_key_id" {
  value = aws_api_gateway_api_key.main.id
}

output "api_key_ssm_parameter" {
  value = aws_ssm_parameter.api_key.name
}

output "ec2_runner_ami_purpose_tag" {
  value = local.ec2_runner_ami_purpose_tag
}

output "ec2_runner_ami_purpose_value" {
  value = local.ec2_runner_ami_purpose_value
}

output "ec2_runner_ami_stable_tag" {
  value = local.ec2_runner_ami_stable_tag
}

output "fargate_cpu_architecture" {
  value = var.fargate_cpu_architecture
}

output "ec2_spot_instance_types" {
  value = var.ec2_spot_instance_types
}

output "ssm_parameter_name_for_latest_ami" {
  value = aws_ssm_parameter.latest_ami.name
}
