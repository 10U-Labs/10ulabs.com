output "arn_for_central_logs_bucket" {
  value = module.central_logs.bucket_arn
}

output "arn_for_central_logs_write_policy" {
  value = module.central_logs.write_policy_arn
}

output "arn_for_github_actions_role" {
  value = module.github_oidc.github_actions_role_arn
}

output "name_for_github_actions_role" {
  value = module.github_oidc.github_actions_role_name
}

output "arn_for_github_pat_parameter" {
  value = aws_ssm_parameter.github_pat.arn
}

output "arn_for_oidc_provider" {
  value = module.github_oidc.oidc_provider_arn
}

output "arn_for_state_bucket" {
  value = aws_s3_bucket.terraform_state.arn
}

output "hosted_zone_id" {
  value = module.domain.hosted_zone_id
}

output "name_for_cloudtrail" {
  value = module.cloudtrail.trail_name
}

output "ssm_parameter_name_for_github_pat" {
  value = aws_ssm_parameter.github_pat.name
}

# ECR Outputs
output "ecr_repository_arn" {
  value = aws_ecr_repository.main.arn
}

output "ecr_repository_name" {
  value = aws_ecr_repository.main.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.main.repository_url
}

# VPC Outputs
output "vpc_id" {
  value = aws_vpc.main.id
}

output "vpc_public_subnet_ids" {
  value = join(",", aws_subnet.public[*].id)
}

# Security Group Outputs
output "runner_security_group_id" {
  value = aws_security_group.runner.id
}
