output "cloudtrail_bucket" {
  value = module.central_logs.bucket_name
}

output "cloudtrail_name" {
  value = module.cloudtrail.trail_name
}

output "github_actions_role_arn" {
  value = module.github_oidc.github_actions_role_arn
}

output "hosted_zone_id" {
  value = module.domain.hosted_zone_id
}

output "oidc_provider_arn" {
  value = module.github_oidc.oidc_provider_arn
}

output "state_bucket_arn" {
  value = aws_s3_bucket.terraform_state.arn
}

output "state_bucket_name" {
  value = aws_s3_bucket.terraform_state.id
}

output "github_pat_parameter_arn" {
  value = aws_ssm_parameter.github_pat.arn
}

output "github_pat_parameter_name" {
  value = aws_ssm_parameter.github_pat.name
}

output "central_logs_bucket_name" {
  value = module.central_logs.bucket_name
}

output "central_logs_bucket_arn" {
  value = module.central_logs.bucket_arn
}

output "central_logs_write_policy_arn" {
  value = module.central_logs.write_policy_arn
}
